import logging
from decimal import Decimal
from django.db import transaction
from ..models import Wallet, WalletUser
from services.moralis_service import MoralisService

logger = logging.getLogger(__name__)

class WalletService:
    """Service class for wallet operations"""
    
    @classmethod
    def get_user_wallets(cls, user, address=None, chain=None):
        """
        Get all wallets for a user with optional filtering
        
        Args:
            user: The user object
            address (str, optional): Filter by wallet address
            chain (str, optional): Filter by blockchain network
            
        Returns:
            QuerySet: Filtered wallet queryset
        """
        # Get all wallet IDs for this user
        wallet_user_query = WalletUser.objects.filter(user=user)
        
        # Apply filters if provided
        if address:
            wallet_user_query = wallet_user_query.filter(wallet__address=address)
        if chain:
            wallet_user_query = wallet_user_query.filter(wallet__chain=chain)
            
        wallet_ids = wallet_user_query.values_list('wallet_id', flat=True)
        
        # Return the wallets
        return Wallet.objects.filter(id__in=wallet_ids)
    
    @classmethod
    def add_wallet(cls, user, address, chain):
        """
        Add a new wallet for a user and fetch its token data
        
        Args:
            user: The user object
            address (str): Wallet address
            chain (str): Blockchain network
            
        Returns:
            tuple: (success_bool, wallet_or_error_message)
        """
        try:
            # Check if wallet already exists for this user
            if WalletUser.objects.filter(
                user=user,
                wallet__address=address,
                wallet__chain=chain
            ).exists():
                return False, "You have already added this wallet address for this blockchain."
                
            # Fetch token data from Moralis
            from .token_service import TokenService  # Import here to avoid circular imports
            success, token_data = MoralisService.get_wallet_tokens(address, chain)
            
            if not success:
                return False, token_data
                
            # Calculate net worth from token data
            tokens = token_data.get('result', [])
            balance_usd = Decimal('0')
            
            for token in tokens:
                usd_value = token.get('usd_value')
                if usd_value:
                    try:
                        balance_usd += Decimal(str(usd_value))
                    except (ValueError, TypeError):
                        # Skip invalid values
                        pass
            
            # Create or update the wallet
            with transaction.atomic():
                wallet, created = Wallet.objects.update_or_create(
                    address=address,
                    chain=chain,
                    defaults={'balance_usd': balance_usd}
                )
                
                # Link wallet to user
                WalletUser.objects.get_or_create(
                    user=user,
                    wallet=wallet
                )
                
                # Process tokens
                if tokens:
                    TokenService.process_wallet_tokens(wallet, token_data, chain)
            
            return True, wallet
            
        except Exception as e:
            logger.exception(f"Error adding wallet: {str(e)}")
            return False, f"Failed to add wallet: {str(e)}"
    
    @classmethod
    def sync_wallet(cls, user, address, chain):
        """
        Sync token data for a specific wallet
        
        Args:
            user: The user object
            address (str): Wallet address
            chain (str): Blockchain network
            
        Returns:
            tuple: (success_bool, wallet_or_error_message)
        """
        try:
            # Verify the user owns this wallet
            try:
                wallet_user = WalletUser.objects.get(
                    user=user,
                    wallet__address=address,
                    wallet__chain=chain
                )
                wallet = wallet_user.wallet
            except WalletUser.DoesNotExist:
                return False, f"Wallet {address} on chain {chain} not found in your portfolio"
                
            # Fetch token data from Moralis
            from .token_service import TokenService  # Import here to avoid circular imports
            success, token_data = MoralisService.get_wallet_tokens(address, chain)
            
            if not success:
                return False, token_data
                
            # Calculate net worth from token data
            tokens = token_data.get('result', [])
            balance_usd = Decimal('0')
            
            for token in tokens:
                usd_value = token.get('usd_value')
                if usd_value:
                    try:
                        balance_usd += Decimal(str(usd_value))
                    except (ValueError, TypeError):
                        # Skip invalid values
                        pass
            
            # Update wallet balance
            wallet.balance_usd = balance_usd
            wallet.save()
            
            # Process tokens
            token_count = 0
            if tokens:
                token_count = TokenService.process_wallet_tokens(wallet, token_data, chain)
            
            return True, {
                'wallet': wallet,
                'token_count': token_count
            }
            
        except Exception as e:
            logger.exception(f"Error syncing wallet: {str(e)}")
            return False, f"Failed to sync wallet: {str(e)}"
    
    @classmethod
    def sync_all_wallets(cls, user):
        """
        Sync token data for all user wallets
        
        Args:
            user: The user object
            
        Returns:
            tuple: (success_bool, results_or_error_message)
        """
        try:
            # Get all wallets for this user
            wallets = cls.get_user_wallets(user)
            
            if not wallets.exists():
                return False, "No wallets found for this user"
            
            results = []
            
            # Process each wallet
            for wallet in wallets:
                success, result = cls.sync_wallet(user, wallet.address, wallet.chain)
                
                if success:
                    results.append({
                        'wallet_address': wallet.address,
                        'chain': wallet.chain,
                        'token_count': result['token_count'] if isinstance(result, dict) else 0,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'wallet_address': wallet.address,
                        'chain': wallet.chain,
                        'error': result,
                        'status': 'failed'
                    })
            
            return True, results
            
        except Exception as e:
            logger.exception(f"Error syncing all wallets: {str(e)}")
            return False, f"Failed to sync all wallets: {str(e)}"
    
    @classmethod
    def remove_wallet(cls, user, address, chain):
        """
        Remove a wallet from a user's portfolio
        
        Args:
            user: The user object
            address (str): Wallet address
            chain (str): Blockchain network
            
        Returns:
            tuple: (success_bool, message_or_error)
        """
        try:
            # Find and delete the wallet-user relationship
            deleted_count, _ = WalletUser.objects.filter(
                user=user,
                wallet__address=address,
                wallet__chain=chain
            ).delete()
            
            # Check if any records were deleted
            if deleted_count == 0:
                return False, f"Wallet with address {address} on chain {chain} not found in your portfolio"
                
            return True, f"Wallet {address} ({chain}) has been removed from your portfolio"
            
        except Exception as e:
            logger.exception(f"Error removing wallet: {str(e)}")
            return False, f"Failed to remove wallet: {str(e)}"
            
    @classmethod
    def get_supported_chains(cls):
        """
        Get a list of supported blockchain networks
        
        Returns:
            list: List of supported chains
        """
        return [
            {'id': chain_id, 'name': chain_name} 
            for chain_name, chain_id in MoralisService.CHAIN_MAPPING.items()
        ]
