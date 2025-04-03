from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from ..serializers import WalletTokenSerializer, AggregatedAssetSerializer
from ..services.token_service import TokenService
import logging

logger = logging.getLogger(__name__)

class TokenListView(APIView):
    """List tokens for the authenticated user's wallets"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get tokens for user wallets with optional filtering"""
        try:
            # Get wallet address and chain from query params
            wallet_address = request.query_params.get('address')
            chain = request.query_params.get('chain')
            
            # Get tokens for user
            wallet_tokens = TokenService.get_user_tokens(
                request.user, wallet_address, chain
            )
            
            # Serialize and return
            serializer = WalletTokenSerializer(wallet_tokens, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Error retrieving tokens: {str(e)}")
            return Response(
                {'error': f"Failed to retrieve tokens: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AssetListView(APIView):
    """View for aggregated asset list across all user wallets"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get aggregated token amounts across wallets"""
        try:
            # Get aggregated assets for user
            assets = TokenService.get_aggregated_assets(request.user)
            
            # Sort by total value (descending)
            assets.sort(key=lambda x: float(x['total_value'] or 0), reverse=True)
            
            # Serialize and return
            serializer = AggregatedAssetSerializer(assets, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Error retrieving aggregated assets: {str(e)}")
            return Response(
                {'error': f"Failed to retrieve aggregated assets: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

