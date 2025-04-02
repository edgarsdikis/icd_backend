# Create a new file: tokens/serializers.py

from rest_framework import serializers
from .models import Token, WalletToken

class TokenSerializer(serializers.ModelSerializer):
    """Serializer for Token model"""
    class Meta:
        model = Token
        fields = [
            'id', 'address', 'chain', 'symbol', 'name', 
            'logo', 'thumbnail', 'usd_price', 
            'usd_price_24h_percent_change', 'usd_price_24h_usd_change'
        ]

class WalletTokenSerializer(serializers.ModelSerializer):
    """Serializer for WalletToken model with nested Token data"""
    token_details = TokenSerializer(source='token', read_only=True)
    
    class Meta:
        model = WalletToken
        fields = [
            'id', 'wallet', 'token', 'token_details', 'chain',
            'token_balance_formatted', 'usd_value', 'usd_value_24h_usd_change'
        ]
        # We want to include token_details when reading but not when writing
        extra_kwargs = {
            'token': {'write_only': True},
            'wallet': {'write_only': True}
        }
