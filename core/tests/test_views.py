from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal
from ..models import AgentTemplate, AgentInstance, Transaction
import json


class UserRegistrationViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-registration')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def test_user_registration(self):
        response = self.client.post(
            self.register_url,
            self.user_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('wallet_address', response.data)
        self.assertTrue(response.data['wallet_address'].startswith('0x'))


class AgentSetupViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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
        self.client.force_authenticate(user=self.user)
        self.setup_url = reverse('agent-setup')
        self.setup_data = {
            'template_id': self.template.id,
            'constraints': {
                'max_price': 500,
                'categories': ['electronics'],
                'preferences': {'brand': 'trusted'}
            },
            'max_budget': '1000.00',
            'allowed_merchants': ['Amazon', 'BestBuy'],
            'bridge_wallet_address': '0x1234567890abcdef1234567890abcdef12345678'
        }

    def test_agent_setup(self):
        response = self.client.post(
            self.setup_url,
            self.setup_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'IDLE')


class TransactionVerificationViewTests(TestCase):
    def setUp(self):
        # Setup code similar to AgentSetupViewTests
        # ... (previous setup code) ...
        self.agent = AgentInstance.objects.create(
            user=self.user,
            template=self.template,
            max_budget=Decimal('1000.00'),
            constraints=self.setup_data['constraints'],
            allowed_merchants=self.setup_data['allowed_merchants'],
            bridge_wallet_address=self.setup_data['bridge_wallet_address']
        )
        self.verify_url = reverse('transaction-verify')
        self.transaction_data = {
            'agent_instance': self.agent.id,
            'amount': '150.00',
            'merchant': 'Amazon',
            'merchant_wallet': '0x1234567890abcdef1234567890abcdef12345678'
        }

    def test_transaction_verification_success(self):
        response = self.client.post(
            self.verify_url,
            self.transaction_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'EXECUTED')
        self.assertTrue('transaction_hash' in response.data)

    def test_transaction_verification_unauthorized_agent(self):
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='other123'
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.post(
            self.verify_url,
            self.transaction_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
