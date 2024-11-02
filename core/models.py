from django.db import models
from django.contrib.auth.models import User


class AgentTemplate(models.Model):
    """Pre-defined agent types available in marketplace"""
    name = models.CharField(max_length=100)  # e.g., "Shopping Assistant"
    description = models.TextField()
    capabilities = models.JSONField()  # e.g., ["shopping", "price_comparison"]

    def __str__(self):
        return self.name


class AgentInstance(models.Model):
    """User's personal instance of an agent"""
    STATUS_CHOICES = [
        ('dormant', 'Dormant'),
        ('active', 'Active'),
        ('executing', 'Executing Task'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(AgentTemplate, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='dormant')
    trust_score = models.IntegerField(default=70)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.template.name}"


class Transaction(models.Model):
    """Record of agent transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    agent_instance = models.ForeignKey(AgentInstance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    merchant = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.agent_instance.template.name} - ${self.amount} ({self.status})"