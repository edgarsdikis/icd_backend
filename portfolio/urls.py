from django.urls import path
from .views import (
    WalletListView, WalletAddView, WalletSyncView, WalletRemoveView,
    TokenListView, AssetListView, get_supported_chains
)

urlpatterns = [
    # Wallet endpoints
    path('wallets/', WalletListView.as_view(), name='wallet-list'),
    path('wallets/add/', WalletAddView.as_view(), name='wallet-add'),
    path('wallets/sync/', WalletSyncView.as_view(), name='wallet-sync'),
    path('wallets/remove/', WalletRemoveView.as_view(), name='wallet-remove'),
    path('wallets/supported-chains/', get_supported_chains, name='supported-chains'),
    
    # Token endpoints
    path('tokens/', TokenListView.as_view(), name='token-list'),
    path('assets/', AssetListView.as_view(), name='asset-list'),
]
