import logging
from decimal import Decimal
from typing import Dict, Any
from django.conf import settings
from .models import AgentInstance, Transaction
from openai import OpenAI
import json

logger = logging.getLogger(__name__)

class ShoppingService:
    """
    Handles shopping task management and verification logic
    """
    def start_shopping_task(self, agent: AgentInstance, 
                           search_criteria: Dict[str, Any]) -> str:
        """
        Initiates a shopping task for an agent
        Returns: task_id (str)
        """
        try:
            # Update agent status to match STATUS_CHOICES
            agent.status = 'SHOPPING'
            agent.save()
            
            # For demo purposes, generate a simple task ID
            task_id = f"task_{agent.id}_{agent.user.id}"
            
            logger.info(f"Started shopping task {task_id} for agent {agent.id}")
            return task_id
            
        except Exception as e:
            agent.status = 'ERROR'
            agent.save()
            logger.error(f"Failed to start shopping task: {str(e)}")
            raise

    def verify_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Verifies transaction safety and compliance
        Returns: Dict with approval status and reason
        """
        try:
            agent = transaction.agent_instance
            
            # Demo verification checks
            checks = {
                'budget_check': transaction.amount <= agent.max_budget,
                'merchant_check': transaction.merchant in agent.allowed_merchants,
                'price_check': self._verify_price_reasonable(transaction)
            }
            
            approved = all(checks.values())
            
            # Update transaction status based on model's STATUS_CHOICES
            transaction.status = 'APPROVED' if approved else 'REJECTED'
            transaction.save()
            
            reason = None if approved else f"Failed checks: {[k for k,v in checks.items() if not v]}"
            
            return {
                'approved': approved,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Transaction verification failed: {str(e)}")
            return {
                'approved': False,
                'reason': f"Verification error: {str(e)}"
            }

    def _verify_price_reasonable(self, transaction: Transaction) -> bool:
        """Demo price verification"""
        if transaction.market_average_price:
            price_diff_percent = (
                (transaction.amount - transaction.market_average_price) 
                / transaction.market_average_price * 100
            )
            return abs(price_diff_percent) <= 15
        return True

class MockBridgeWalletService:  # Renamed from BridgeWalletService
    """
    Mock implementation of Bridge API integration for demo purposes
    In production, this would integrate with actual Bridge API
    """
    def create_wallet(self, user) -> str:
        """Mock wallet creation"""
        mock_address = f"0x{user.id:040x}"  # Demo wallet address
        logger.info(f"Created mock wallet {mock_address} for user {user.id}")
        return mock_address

    def execute_transfer(self, from_wallet: str, to_wallet: str, 
                        amount: Decimal) -> str:
        """Mock USDC transfer"""
        # In production, this would call Bridge API
        mock_tx_hash = f"0x{hash(f'{from_wallet}{to_wallet}{amount}'):064x}"
        logger.info(f"Mock transfer: {amount} USDC from {from_wallet} to {to_wallet}")
        return mock_tx_hash

class TrustScoreService:
    """
    Handles trust score calculations and updates
    """
    def update_score(self, agent: AgentInstance, event_type: str) -> None:
        """
        Updates agent trust score based on events
        """
        score_impacts = {
            'SUCCESSFUL_TRANSACTION': 5,
            'FAILED_TRANSACTION': -10,
            'PRICE_SAVING': 2,
            'SUSPICIOUS_ACTIVITY': -15
        }
        
        if event_type in score_impacts:
            impact = score_impacts[event_type]
            # Use validators from model
            new_score = max(0, min(100, agent.trust_score + impact))
            
            agent.trust_score = new_score
            agent.save()
            
            logger.info(
                f"Updated trust score for agent {agent.id}: {new_score} "
                f"(impact: {impact})"
            )

class PromptProcessingService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_SETTINGS['API_KEY'])
        self.logger = logging.getLogger(__name__)

    def process_shopping_prompt(self, prompt: str) -> Dict[str, Any]:
        """Convert natural language prompt into structured shopping constraints."""
        try:
            self.logger.info(f"Processing shopping prompt: '{prompt}'")
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_SETTINGS.get('MODEL', 'gpt-4'),
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            constraints = json.loads(response.choices[0].message.content)
            self.logger.info(f"Successfully generated constraints from OpenAI: {json.dumps(constraints, indent=2)}")
            return constraints
            
        except Exception as e:
            self.logger.error(f"OpenAI error ({type(e).__name__}): {str(e)}")
            self.logger.warning("⚠️ Using default constraints due to OpenAI error")
            default_constraints = self._get_default_constraints()
            self.logger.info(f"Default constraints being used: {json.dumps(default_constraints, indent=2)}")
            return default_constraints

    def _get_default_constraints(self) -> Dict[str, Any]:
        """Get default constraints when OpenAI processing fails."""
        return {
            "max_price": 500,
            "categories": ["general"],
            "preferences": {
                "brand": "any",
                "condition": "new",
                "shipping": "standard"
            },
            "_source": "default"  # Added to indicate these are default constraints
        }

    def _get_system_prompt(self) -> str:
        """Define the system prompt for constraint generation."""
        return """
        You are a shopping assistant that converts user requirements into structured JSON.
        Convert the shopping request into this exact format:
        {
            "max_price": <integer in USD>,
            "categories": [<list of relevant product categories>],
            "preferences": {
                "brand": <"trusted", "any", or specific brand>,
                "condition": <"new", "used", "any">,
                "shipping": <"fast", "standard", "any">
            }
        }
        """