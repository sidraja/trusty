from django.urls import path
from .views import (
    UserRegistrationView,
    AgentSetupView,
    AgentShoppingView,
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-registration'),
    path('agents/setup/', AgentSetupView.as_view(), name='agent-setup'),
    path('agents/<int:agent_id>/shop/', AgentShoppingView.as_view(), name='agent-shopping'),
]