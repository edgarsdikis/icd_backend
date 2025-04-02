# tokens/urls.py
from django.urls import path
from .views import TokenView, TokenSyncView, TokenSyncAllView, get_supported_token_standards

urlpatterns = [
    # Endpoint for listing tokens (GET)
    path('list/', TokenView.as_view(), name='list-tokens'),
    
    # Endpoint for syncing tokens for a specific wallet (POST)
    path('sync/', TokenSyncView.as_view(), name='sync-tokens'),
    
    # Endpoint for syncing tokens for all wallets (POST)
    path('sync-all/', TokenSyncAllView.as_view(), name='sync-all-tokens'),
    
    # Endpoint for supported token standards (GET)
    path('supported-standards/', get_supported_token_standards, name='supported-token-standards'),
]
