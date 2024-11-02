from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class AgentTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    capabilities = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [models.Index(fields=['name'])]

class AgentInstance(models.Model):
    STATUS_CHOICES = [
        ('IDLE', 'Idle'),
        ('SHOPPING', 'Shopping'),
        ('VERIFYING', 'Verifying'),
        ('COMPLETED', 'Completed'),
        ('ERROR', 'Error')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(AgentTemplate, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IDLE')
    trust_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=50
    )
    constraints = models.JSONField(default=dict)  # Shopping constraints
    max_budget = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_merchants = models.JSONField(default=list)
    bridge_wallet_address = models.CharField(max_length=255, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['trust_score'])
        ]

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFYING', 'Verifying'),
        ('APPROVED', 'Approved'),
        ('EXECUTED', 'Executed'),
        ('REJECTED', 'Rejected')
    ]
    
    agent_instance = models.ForeignKey(AgentInstance, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    merchant = models.CharField(max_length=255)
    merchant_wallet = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Price comparison fields
    market_average_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    lowest_price_found = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_difference_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    # Transaction details
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True)
    transaction_hash = models.CharField(max_length=255, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['agent_instance', 'status']),
            models.Index(fields=['created_at'])
        ]

class PriceComparison(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    merchant_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)