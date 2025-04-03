from rest_framework import serializers
from ..models import Token, WalletToken

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

class AggregatedAssetSerializer(serializers.Serializer):
    """Serializer for aggregated token data across wallets"""
    symbol = serializers.CharField()
    name = serializers.CharField()
    chain = serializers.CharField()
    price = serializers.DecimalField(max_digits=30, decimal_places=18, allow_null=True)
    price_24h_change_percent = serializers.DecimalField(max_digits=30, decimal_places=18, allow_null=True)
    price_24h_change_usd = serializers.DecimalField(max_digits=30, decimal_places=18, allow_null=True)
    logo = serializers.URLField(allow_null=True)
    thumbnail = serializers.URLField(allow_null=True)
    total_amount = serializers.DecimalField(max_digits=30, decimal_places=18)
    total_value = serializers.DecimalField(max_digits=30, decimal_places=18)
    total_value_24h_change = serializers.DecimalField(max_digits=30, decimal_places=18, allow_null=True)
