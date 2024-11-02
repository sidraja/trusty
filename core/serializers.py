from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AgentTemplate, AgentInstance, Transaction, PriceComparison

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class AgentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTemplate
        fields = '__all__'

class AgentInstanceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    template = AgentTemplateSerializer(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=AgentTemplate.objects.all(),
        write_only=True,
        source='template'
    )
    
    class Meta:
        model = AgentInstance
        fields = (
            'id', 'user', 'template', 'template_id', 'status', 
            'trust_score', 'constraints', 'max_budget', 
            'allowed_merchants', 'bridge_wallet_address'
        )
        read_only_fields = ('status', 'trust_score')
    
    def validate_constraints(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Constraints must be a dictionary")
            
        required_keys = {'max_price', 'categories', 'preferences'}
        if not all(key in value for key in required_keys):
            raise serializers.ValidationError(
                f"Constraints must include: {', '.join(required_keys)}"
            )
        return value
    
    def validate_max_budget(self, value):
        if value <= 0:
            raise serializers.ValidationError("Max budget must be greater than 0")
        return value

class PriceComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceComparison
        fields = ('merchant_name', 'price', 'url', 'timestamp')
        read_only_fields = ('timestamp',)

class TransactionSerializer(serializers.ModelSerializer):
    price_comparisons = PriceComparisonSerializer(many=True, read_only=True)
    savings_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'agent_instance', 'amount', 'merchant',
            'merchant_wallet', 'status', 'market_average_price',
            'lowest_price_found', 'price_difference_percentage',
            'created_at', 'executed_at', 'transaction_hash',
            'price_comparisons', 'savings_percentage'
        )
        read_only_fields = (
            'status', 'market_average_price', 'lowest_price_found',
            'price_difference_percentage', 'created_at', 'executed_at',
            'transaction_hash'
        )
    
    def get_savings_percentage(self, obj):
        if obj.market_average_price and obj.amount:
            savings = (obj.market_average_price - obj.amount) / obj.market_average_price * 100
            return round(savings, 2)
        return None
    
    def validate(self, data):
        # Verify amount is within agent's max budget
        agent_instance = data['agent_instance']
        if data['amount'] > agent_instance.max_budget:
            raise serializers.ValidationError(
                "Transaction amount exceeds agent's maximum budget"
            )
        
        # Verify merchant is in allowed list
        if data['merchant'] not in agent_instance.allowed_merchants:
            raise serializers.ValidationError(
                "Merchant not in allowed merchants list"
            )
        
        return data

class AgentStatusSerializer(serializers.ModelSerializer):
    """Simplified serializer for status checks"""
    latest_transaction = TransactionSerializer(read_only=True)
    
    class Meta:
        model = AgentInstance
        fields = ('id', 'status', 'trust_score', 'latest_transaction')

class AgentSetupSerializer(serializers.ModelSerializer):
    """Serializer for initial agent setup"""
    class Meta:
        model = AgentInstance
        fields = (
            'template_id', 'constraints', 'max_budget',
            'allowed_merchants', 'bridge_wallet_address'
        )
        
    def validate_bridge_wallet_address(self, value):
        # Basic Ethereum address validation
        if not value.startswith('0x') or len(value) != 42:
            raise serializers.ValidationError(
                "Invalid Ethereum wallet address format"
            )
        return value