# tokens/admin.py
from django.contrib import admin
from .models import Token, WalletToken

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """Admin configuration for Token model"""
    list_display = ('symbol', 'name', 'chain', 'address', 'usd_price')
    search_fields = ('symbol', 'name', 'address')
    list_filter = ('chain',)
    ordering = ('chain', 'symbol')

@admin.register(WalletToken)
class WalletTokenAdmin(admin.ModelAdmin):
    """Admin configuration for WalletToken model"""
    list_display = ('wallet_address', 'token_symbol', 'chain', 'token_balance_formatted', 'usd_value')
    search_fields = ('wallet__address', 'token__symbol', 'token__name')
    list_filter = ('chain',)
    
    # Custom display methods to access nested properties
    @admin.display(description='Wallet Address')
    def wallet_address(self, obj):
        return obj.wallet.address
    
    @admin.display(description='Token')
    def token_symbol(self, obj):
        return f"{obj.token.symbol} ({obj.token.name})"
