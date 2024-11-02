import logging
from decimal import Decimal
from typing import Dict, Any
from django.conf import settings
from .models import AgentInstance, Transaction

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