from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from ..models import AgentTemplate, AgentInstance, Transaction, PriceComparison

class AgentTemplateTests(TestCase):
    def setUp(self):
        self.template_data = {
            'name': 'Shopping Assistant',
            'description': 'Helps find the best deals',
            'capabilities': {
                'price_comparison': True,
                'merchant_verification': True,
                'automated_checkout': False
            }
        }

    def test_create_template(self):
        template = AgentTemplate.objects.create(**self.template_data)
        self.assertEqual(template.name, self.template_data['name'])
        self.assertTrue(template.capabilities['price_comparison'])

class AgentInstanceTests(TestCase):
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
        self.agent_data = {
            'user': self.user,
            'template': self.template,
            'max_budget': Decimal('1000.00'),
            'constraints': {
                'max_price': 500,
                'categories': ['electronics'],
                'preferences': {'brand': 'trusted'}
            },
            'allowed_merchants': ['Amazon', 'BestBuy']
        }

    def test_create_agent(self):
        agent = AgentInstance.objects.create(**self.agent_data)
        self.assertEqual(agent.status, 'IDLE')
        self.assertEqual(agent.trust_score, 50)

    def test_max_budget_validation(self):
        self.agent_data['max_budget'] = Decimal('-100.00')
        with self.assertRaises(ValidationError):
            agent = AgentInstance.objects.create(**self.agent_data)
            agent.full_clean()

class TransactionTests(TestCase):
    def setUp(self):
        # Setup code from AgentInstanceTests
        # ... (previous setup code) ...
        self.agent = AgentInstance.objects.create(**self.agent_data)
        self.transaction_data = {
            'agent_instance': self.agent,
            'amount': Decimal('150.00'),
            'merchant': 'Amazon',
            'merchant_wallet': '0x1234567890abcdef1234567890abcdef12345678',
            'market_average_price': Decimal('180.00')
        }

    def test_create_transaction(self):
        transaction = Transaction.objects.create(**self.transaction_data)
        self.assertEqual(transaction.status, 'PENDING')
        self.assertIsNone(transaction.executed_at)

    def test_price_comparison(self):
        transaction = Transaction.objects.create(**self.transaction_data)
        comparison = PriceComparison.objects.create(
            transaction=transaction,
            merchant_name='BestBuy',
            price=Decimal('170.00'),
            url='https://bestbuy.com/test'
        )
        self.assertEqual(comparison.merchant_name, 'BestBuy') 