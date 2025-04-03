from rest_framework import serializers
from ..models import Wallet, WalletUser

class AddWalletSerializer(serializers.Serializer):
    """Serializer for adding a new wallet"""
    address = serializers.CharField(
        max_length=255, 
        min_length=26,  # Basic length validation
    )
    chain = serializers.CharField(max_length=50)
    
    def validate(self, attrs):
        """Validate the inputs"""
        # Check if request exists in context
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Authentication required")
        
        return attrs

class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet data"""
    class Meta:
        model = Wallet
        fields = ['address', 'balance_usd', 'chain', 'synced_at']
