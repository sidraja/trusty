from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from core.models import AgentTemplate, AgentInstance


class AgentInstanceCreationTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test template
        self.template = AgentTemplate.objects.create(
            name='Test Template',
            description='Test Description',
            capabilities={'test': True}
        )

    def test_create_agent_instance(self):
        try:
            agent = AgentInstance.objects.create(
                user=self.user,
                template=self.template,
                max_budget=Decimal('1000.00'),
                constraints={
                    'max_price': 500,
                    'categories': ['electronics'],
                    'preferences': {'brand': 'trusted'}
                },
                allowed_merchants=['Amazon', 'BestBuy'],
                bridge_wallet_address='0x1234567890abcdef1234567890abcdef12345678'
            )
            
            # Verify the agent was created with correct values
            self.assertEqual(agent.status, 'IDLE')
            self.assertEqual(agent.trust_score, 50)
            self.assertEqual(agent.user, self.user)
            self.assertEqual(agent.template, self.template)
            self.assertEqual(agent.max_budget, Decimal('1000.00'))
            
            # Verify it's in the database
            saved_agent = AgentInstance.objects.get(id=agent.id)
            self.assertEqual(saved_agent.max_budget, Decimal('1000.00'))
            
        except Exception as e:
            self.fail(f"Failed to create agent instance: {str(e)}")


class AgentTemplateTest(TestCase):
    def test_create_template(self):
        template = AgentTemplate.objects.create(
            name='Test Template',
            description='Test Description',
            capabilities={'test': True}
        )
        
        self.assertEqual(template.name, 'Test Template')
        self.assertTrue('test' in template.capabilities)
