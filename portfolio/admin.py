from django.contrib import admin
from .models import Wallet, WalletUser, Token, WalletToken

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin configuration for Wallet model"""
    list_display = ('address', 'chain', 'balance_usd', 'synced_at')
    search_fields = ('address', 'chain')
    list_filter = ('chain', 'synced_at')
    readonly_fields = ('synced_at',)

@admin.register(WalletUser)
class WalletUserAdmin(admin.ModelAdmin):
    """Admin configuration for WalletUser model"""
    list_display = ('user', 'wallet_address', 'wallet_chain')
    search_fields = ('user__username', 'wallet__address')
    list_filter = ('wallet__chain',)
    
    @admin.display(description='Wallet Address')
    def wallet_address(self, obj):
        return obj.wallet.address
    
    @admin.display(description='Chain')
    def wallet_chain(self, obj):
        return obj.wallet.chain

@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """Admin configuration for Token model"""
    list_display = ('symbol', 'name', 'chain', 'address', 'usd_price', 'updated_at')
    search_fields = ('symbol', 'name', 'address')
    list_filter = ('chain',)
    ordering = ('chain', 'symbol')

@admin.register(WalletToken)
class WalletTokenAdmin(admin.ModelAdmin):
    """Admin configuration for WalletToken model"""
    list_display = ('wallet_address', 'token_symbol', 'chain', 'token_balance_formatted', 'usd_value')
    search_fields = ('wallet__address', 'token__symbol', 'token__name')
    list_filter = ('chain',)
    
    @admin.display(description='Wallet Address')
    def wallet_address(self, obj):
        return obj.wallet.address
    
    @admin.display(description='Token')
    def token_symbol(self, obj):
        return f"{obj.token.symbol} ({obj.token.name})"
