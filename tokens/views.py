# tokens/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from wallets.models import Wallet, WalletUser
from .models import Token, WalletToken
from .serializers import WalletTokenSerializer
from wallets.services import MoralisService
import logging

logger = logging.getLogger(__name__)

class TokenView(APIView):
    """Base API endpoint for token operations"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get tokens for user wallets with optional filtering"""
        try:
            # Get wallet address and chain from query params
            wallet_address = request.query_params.get('address')
            chain = request.query_params.get('chain')
            
            # Get all wallet IDs for this user
            wallet_user_query = WalletUser.objects.filter(user=request.user)
            
            # Apply filters if provided
            if wallet_address:
                wallet_user_query = wallet_user_query.filter(wallet__address=wallet_address)
            if chain:
                wallet_user_query = wallet_user_query.filter(wallet__chain=chain)
                
            wallet_ids = wallet_user_query.values_list('wallet_id', flat=True)
            
            if not wallet_ids.exists():
                return Response(
                    {'error': 'No matching wallets found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get wallet tokens
            wallet_tokens = WalletToken.objects.filter(wallet_id__in=wallet_ids)
            
            # Serialize and return
            serializer = WalletTokenSerializer(wallet_tokens, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Error retrieving wallet tokens: {str(e)}")
            return Response(
                {'error': f"Failed to retrieve wallet tokens: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def sync(self, request):
        """Sync tokens for a specific wallet"""
        try:
            # Get wallet address and chain from request data
            wallet_address = request.data.get('address')
            chain = request.data.get('chain')
                
            if not wallet_address or not chain:
                return Response(
                    {'error': 'Both wallet address and chain are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verify the user owns this wallet
            try:
                wallet_user = WalletUser.objects.get(
                    user=request.user,
                    wallet__address=wallet_address,
                    wallet__chain=chain
                )
                wallet = wallet_user.wallet
            except WalletUser.DoesNotExist:
                return Response(
                    {'error': f"Wallet {wallet_address} on chain {chain} not found in your portfolio"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            # Call Moralis to get token data
            success, result = MoralisService.get_wallet_tokens(wallet_address, chain)
            
            if not success:
                return Response(
                    {'error': result if result else 'Failed to retrieve token data'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Process token data
            tokens_updated = self._process_token_data(wallet, result, chain)
            
            return Response({
                'message': f"Successfully synced {tokens_updated} tokens for wallet {wallet_address} on chain {chain}",
                'tokens_count': tokens_updated
            })
            
        except Exception as e:
            logger.exception(f"Error syncing wallet tokens: {str(e)}")
            return Response(
                {'error': f"Failed to sync wallet tokens: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def sync_all(self, request):
        """Sync tokens for all wallets"""
        try:
            # Get all wallets for this user
            wallet_users = WalletUser.objects.filter(user=request.user)
            
            if not wallet_users.exists():
                return Response(
                    {'message': 'No wallets found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            results = []
            
            # Process each wallet
            for wallet_user in wallet_users:
                wallet = wallet_user.wallet
                
                # Call Moralis to get token data
                success, result = MoralisService.get_wallet_tokens(wallet.address, wallet.chain)
                
                if success:
                    tokens_updated = self._process_token_data(wallet, result, wallet.chain)
                    results.append({
                        'wallet_address': wallet.address,
                        'chain': wallet.chain,
                        'tokens_updated': tokens_updated,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'wallet_address': wallet.address,
                        'chain': wallet.chain,
                        'error': result,
                        'status': 'failed'
                    })
            
            return Response({
                'message': f"Token sync completed for {len(results)} wallets",
                'results': results
            })
            
        except Exception as e:
            logger.exception(f"Error syncing all wallet tokens: {str(e)}")
            return Response(
                {'error': f"Failed to sync all wallet tokens: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_token_data(self, wallet, data, chain):
        """Process token data from Moralis API response"""
        tokens_processed = 0
        
        # Clear existing tokens for this wallet to avoid duplicates
        WalletToken.objects.filter(wallet=wallet, chain=chain).delete()
        
        # Process each token in the response - tokens are in the "result" field, not "tokens"
        tokens = data.get('result', [])
        logger.info(f"Found {len(tokens)} tokens for wallet {wallet.address} on chain {chain}")
        
        for token_data in tokens:
            try:
                # Extract token information with proper field names
                token_address = token_data.get('token_address')
                if not token_address:
                    logger.warning(f"Missing token_address in token data: {token_data}")
                    continue
                    
                # Get or create the token with the correct field mappings
                token, _ = Token.objects.update_or_create(
                    address=token_address,
                    chain=chain,
                    defaults={
                        'symbol': token_data.get('symbol', ''),
                        'name': token_data.get('name', ''),
                        'logo': token_data.get('logo'),
                        'thumbnail': token_data.get('thumbnail'),
                        'usd_price': token_data.get('usd_price'),
                        'usd_price_24h_percent_change': token_data.get('usd_price_24hr_percent_change'),
                        'usd_price_24h_usd_change': token_data.get('usd_price_24hr_usd_change')
                    }
                )
                
                # Create the wallet-token relationship
                WalletToken.objects.create(
                    wallet=wallet,
                    token=token,
                    chain=chain,
                    token_balance_formatted=token_data.get('balance_formatted'),
                    usd_value=token_data.get('usd_value'),
                    usd_value_24h_usd_change=token_data.get('usd_value_24hr_usd_change')
                )
                
                tokens_processed += 1
                
            except Exception as e:
                # Log error but continue processing other tokens
                logger.error(f"Error processing token {token_data.get('token_address')}: {str(e)}")
                
        return tokens_processed


class TokenSyncView(TokenView):
    """API endpoint specifically for token synchronization"""
    def post(self, request):
        """Override post method to call sync"""
        return self.sync(request)


class TokenSyncAllView(TokenView):
    """API endpoint specifically for syncing all tokens"""
    def post(self, request):
        """Override post method to call sync_all"""
        return self.sync_all(request)


# Function for getting supported token standards (similar to supported chains)
@api_view(['GET'])
def get_supported_token_standards(_request):
    """Return a list of supported token standards"""
    return Response({
        'supported_standards': [
            {'id': 'erc20', 'name': 'ERC-20'},
            {'id': 'erc721', 'name': 'ERC-721 (NFT)'},
            {'id': 'erc1155', 'name': 'ERC-1155 (Multi Token)'}
            # Add other standards as needed
        ]
    })
