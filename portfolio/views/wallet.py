from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from ..serializers import AddWalletSerializer, WalletSerializer
from ..services.wallet_service import WalletService
import logging

logger = logging.getLogger(__name__)

class WalletListView(APIView):
    """List all wallets for the authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all wallets for the authenticated user"""
        try:
            # Get wallets for user
            wallets = WalletService.get_user_wallets(request.user)
            
            # Serialize and return
            serializer = WalletSerializer(wallets, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Error retrieving wallets: {str(e)}")
            return Response(
                {'error': f"Failed to retrieve wallets: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WalletAddView(APIView):
    """Add a new wallet for the authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Add a new wallet"""
        # Validate request data
        serializer = AddWalletSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Extract validated data
        address = serializer.validated_data['address']
        chain = serializer.validated_data['chain']
        
        # Add wallet
        success, result = WalletService.add_wallet(request.user, address, chain)
        
        if not success:
            return Response(
                {'error': result},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Return the wallet data
        serializer = WalletSerializer(result)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

class WalletSyncView(APIView):
    """Sync wallet data for the authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Sync a specific wallet"""
        # Extract address and chain
        address = request.data.get('address')
        chain = request.data.get('chain')
        
        if not address or not chain:
            return Response(
                {'error': 'Both wallet address and chain are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Sync wallet
        success, result = WalletService.sync_wallet(request.user, address, chain)
        
        if not success:
            return Response(
                {'error': result},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Return the updated wallet data
        serializer = WalletSerializer(result['wallet'])
        return Response({
            'wallet': serializer.data,
            'token_count': result['token_count']
        })
    
    def get(self, request):
        """Sync all wallets for the user"""
        # Sync all wallets
        success, result = WalletService.sync_all_wallets(request.user)
        
        if not success:
            return Response(
                {'error': result},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Return the sync results
        return Response({
            'message': f"Successfully synced {len(result)} wallets",
            'results': result
        })

class WalletRemoveView(APIView):
    """Remove a wallet for the authenticated user"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Remove a wallet"""
        # Extract address and chain
        address = request.data.get('address')
        chain = request.data.get('chain')
        
        if not address or not chain:
            return Response(
                {'error': 'Both wallet address and chain are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Remove wallet
        success, message = WalletService.remove_wallet(request.user, address, chain)
        
        if not success:
            return Response(
                {'error': message},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Return success message
        return Response({'message': message})

@api_view(['GET'])
def get_supported_chains(request):
    """Return a list of supported blockchain networks"""
    chains = WalletService.get_supported_chains()
    return Response({'supported_chains': chains})
