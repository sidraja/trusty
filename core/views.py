from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from .models import AgentInstance, Transaction
from .serializers import (
    UserSerializer, AgentInstanceSerializer, TransactionSerializer,
    AgentStatusSerializer, AgentSetupSerializer
)
from .services import ShoppingService, BridgeWalletService, TrustScoreService

logger = logging.getLogger(__name__)

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Register a new user with email, username, and password.
        Also creates a Bridge wallet for the user.
        """
        serializer = UserSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                user = serializer.save()
                # Initialize Bridge wallet
                wallet_service = BridgeWalletService()
                wallet_address = wallet_service.create_wallet(user)
                
                return Response({
                    'user': serializer.data,
                    'wallet_address': wallet_address
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            return Response({
                'error': 'Registration failed',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AgentSetupView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Configure a new shopping agent instance for the user.
        Requires template_id, constraints, and budget information.
        """
        serializer = AgentSetupSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                agent_instance = AgentInstance.objects.create(
                    user=request.user,
                    **serializer.validated_data
                )
                
                response_serializer = AgentInstanceSerializer(agent_instance)
                return Response(
                    response_serializer.data, 
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            logger.error(f"Agent setup failed: {str(e)}")
            return Response({
                'error': 'Setup failed',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AgentShoppingView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, agent_id):
        """
        Start a shopping task for the specified agent.
        Initiates price comparison and merchant verification.
        """
        agent = get_object_or_404(
            AgentInstance, 
            id=agent_id, 
            user=request.user
        )
        
        if agent.status != 'IDLE':
            return Response({
                'error': 'Agent is already processing a task'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            shopping_service = ShoppingService()
            task_id = shopping_service.start_shopping_task(
                agent,
                request.data.get('search_criteria', {})
            )
            
            return Response({
                'task_id': task_id,
                'status': 'SHOPPING'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Shopping task failed: {str(e)}")
            return Response({
                'error': 'Shopping task failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AgentStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, agent_id):
        """
        Check the current status of an agent and its latest transaction.
        """
        agent = get_object_or_404(
            AgentInstance.objects.select_related('latest_transaction'),
            id=agent_id,
            user=request.user
        )
        
        serializer = AgentStatusSerializer(agent)
        return Response(serializer.data)

class TransactionVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Verify and execute a transaction using Bridge API.
        Requires transaction details and performs safety checks.
        """
        serializer = TransactionSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            
            # Verify agent ownership
            agent = serializer.validated_data['agent_instance']
            if agent.user != request.user:
                raise ValidationError("Not authorized for this agent")
            
            with transaction.atomic():
                # Create transaction record
                transaction_obj = serializer.save(status='VERIFYING')
                
                # Perform verification
                shopping_service = ShoppingService()
                trust_service = TrustScoreService()
                
                verification_result = shopping_service.verify_transaction(
                    transaction_obj
                )
                
                if verification_result['approved']:
                    # Execute USDC transfer
                    wallet_service = BridgeWalletService()
                    tx_hash = wallet_service.execute_transfer(
                        from_wallet=agent.bridge_wallet_address,
                        to_wallet=transaction_obj.merchant_wallet,
                        amount=transaction_obj.amount
                    )
                    
                    # Update transaction and trust score
                    transaction_obj.status = 'EXECUTED'
                    transaction_obj.transaction_hash = tx_hash
                    transaction_obj.save()
                    
                    trust_service.update_score(agent, 'SUCCESSFUL_TRANSACTION')
                    
                    return Response({
                        'status': 'EXECUTED',
                        'transaction_hash': tx_hash
                    })
                else:
                    transaction_obj.status = 'REJECTED'
                    transaction_obj.save()
                    return Response({
                        'status': 'REJECTED',
                        'reason': verification_result['reason']
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            logger.error(f"Transaction verification failed: {str(e)}")
            return Response({
                'error': 'Verification failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)