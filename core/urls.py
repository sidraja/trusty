from django.urls import path
from .views import (
    UserRegistrationView,
    AgentSetupView,
    AgentShoppingView,
    AgentStatusView,
    TransactionVerificationView,
    StandalonePromptProcessingView
)

app_name = 'core'

urlpatterns = [
    path('auth/register/', UserRegistrationView.as_view(), name='user-registration'),
    path('agents/setup/', AgentSetupView.as_view(), name='agent-setup'),
    path('agents/<int:agent_id>/shop/', AgentShoppingView.as_view(), name='agent-shopping'),
    path('agents/<int:agent_id>/status/', AgentStatusView.as_view(), name='agent-status'),
    path('transactions/verify/', TransactionVerificationView.as_view(), name='transaction-verify'),
    path('prompt/process/', StandalonePromptProcessingView.as_view(), name='prompt-process'),
]