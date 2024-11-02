from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from ..models import AgentTemplate, AgentInstance, Transaction
from ..services import ShoppingService, MockBridgeWalletService, TrustScoreService, PromptProcessingService
from unittest.mock import patch, MagicMock

class ShoppingServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.template = AgentTemplate.objects.create(
            name='Test Template',
            description='Test Description',
            capabilities={'test': True}
        )
        self.agent = AgentInstance.objects.create(
            user=self.user,
            template=self.template,
            max_budget=Decimal('1000.00'),
            constraints={
                'max_price': 500,
                'categories': ['electronics'],
                'preferences': {'brand': 'trusted'}
            },
            allowed_merchants=['Amazon', 'BestBuy']
        )
        self.shopping_service = ShoppingService()

    def test_start_shopping_task(self):
        task_id = self.shopping_service.start_shopping_task(
            self.agent,
            {'category': 'electronics'}
        )
        self.assertTrue(task_id.startswith('task_'))
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.status, 'SHOPPING')

    def test_verify_transaction_success(self):
        transaction = Transaction.objects.create(
            agent_instance=self.agent,
            amount=Decimal('150.00'),
            merchant='Amazon',
            merchant_wallet='0x1234567890abcdef1234567890abcdef12345678',
            market_average_price=Decimal('180.00')
        )
        result = self.shopping_service.verify_transaction(transaction)
        self.assertTrue(result['approved'])

class MockBridgeWalletServiceTests(TestCase):
    def setUp(self):
        self.wallet_service = MockBridgeWalletService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_wallet(self):
        wallet_address = self.wallet_service.create_wallet(self.user)
        self.assertTrue(wallet_address.startswith('0x'))
        self.assertEqual(len(wallet_address), 42)

    def test_execute_transfer(self):
        from_wallet = '0x1234567890abcdef1234567890abcdef12345678'
        to_wallet = '0x9876543210abcdef1234567890abcdef12345678'
        amount = Decimal('100.00')
        tx_hash = self.wallet_service.execute_transfer(
            from_wallet,
            to_wallet,
            amount
        )
        self.assertTrue(tx_hash.startswith('0x'))

class TrustScoreServiceTests(TestCase):
    def setUp(self):
        # Setup code similar to ShoppingServiceTests
        # ... (previous setup code) ...
        self.trust_service = TrustScoreService()

    def test_update_score(self):
        initial_score = self.agent.trust_score
        self.trust_service.update_score(self.agent, 'SUCCESSFUL_TRANSACTION')
        self.agent.refresh_from_db()
        self.assertTrue(self.agent.trust_score > initial_score)

    def test_score_limits(self):
        # Test upper limit
        self.agent.trust_score = 98
        self.agent.save()
        self.trust_service.update_score(self.agent, 'SUCCESSFUL_TRANSACTION')
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.trust_score, 100)

        # Test lower limit
        self.agent.trust_score = 5
        self.agent.save()
        self.trust_service.update_score(self.agent, 'FAILED_TRANSACTION')
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.trust_score, 0) 

class PromptProcessingServiceTests(TestCase):
    def setUp(self):
        self.service = PromptProcessingService()
        self.test_prompt = "I want to buy a gaming laptop under $2000"
        self.expected_constraints = {
            'max_price': 2000,
            'categories': ['electronics', 'laptops', 'gaming'],
            'preferences': {
                'brand': 'trusted',
                'condition': 'new',
                'shipping': 'standard'
            }
        }

    @patch('openai.OpenAI')
    def test_process_shopping_prompt(self, mock_openai):
        # Configure mock
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = (
            '{"max_price": 2000, "categories": ["electronics", "laptops", "gaming"], '
            '"preferences": {"brand": "trusted", "condition": "new", "shipping": "standard"}}'
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        # Test the service
        result = self.service.process_shopping_prompt(self.test_prompt)
        
        self.assertEqual(result, self.expected_constraints)
        mock_client.chat.completions.create.assert_called_once()

    def test_process_shopping_prompt_error_handling(self):
        with patch('openai.OpenAI') as mock_openai:
            # Configure mock to raise an exception
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            # Test error handling
            result = self.service.process_shopping_prompt(self.test_prompt)
            
            # Should return default constraints on error
            self.assertTrue('max_price' in result)
            self.assertTrue('categories' in result)
            self.assertTrue('preferences' in result) 