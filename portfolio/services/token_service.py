import logging
from decimal import Decimal
from django.db import transaction
from ..models import Token, WalletToken

logger = logging.getLogger(__name__)

class TokenService:
    """Service class for token operations"""
    
    @classmethod
    def get_wallet_tokens(cls, wallet_ids):
        """
        Get tokens for specific wallets
        
        Args:
            wallet_ids: List of wallet IDs
            
        Returns:
            QuerySet: WalletToken queryset
        """
        return WalletToken.objects.filter(wallet_id__in=wallet_ids)
    
    @classmethod
    def get_user_tokens(cls, user, wallet_address=None, chain=None):
        """
        Get all tokens for a user's wallets with optional filtering
        
        Args:
            user: The user object
            wallet_address (str, optional): Filter by wallet address
            chain (str, optional): Filter by blockchain network
            
        Returns:
            QuerySet: Filtered WalletToken queryset
        """
        from ..services.wallet_service import WalletService
        
        # Get wallet IDs for this user
        wallets = WalletService.get_user_wallets(user, wallet_address, chain)
        wallet_ids = wallets.values_list('id', flat=True)
        
        # Return the wallet tokens
        return cls.get_wallet_tokens(wallet_ids)
    
    @classmethod
    def get_aggregated_assets(cls, user):
        """
        Get aggregated token balances across all wallets for a user
        
        Args:
            user: The user object
            
        Returns:
            list: Aggregated token data
        """
        from ..services.wallet_service import WalletService
        
        # Get all wallet IDs for this user
        wallets = WalletService.get_user_wallets(user)
        wallet_ids = wallets.values_list('id', flat=True)
        
        if not wallet_ids.exists():
            return []
        
        # Get all tokens for these wallets
        wallet_tokens = cls.get_wallet_tokens(wallet_ids)
        
        # Group tokens by symbol and chain, and aggregate balances
        aggregated = {}
        
        for wt in wallet_tokens:
            key = (wt.token.symbol, wt.chain)
            
            if key not in aggregated:
                aggregated[key] = {
                    'symbol': wt.token.symbol,
                    'name': wt.token.name,
                    'chain': wt.chain,
                    'price': wt.token.usd_price,
                    'price_24h_change_percent': wt.token.usd_price_24h_percent_change,
                    'price_24h_change_usd': wt.token.usd_price_24h_usd_change,
                    'logo': wt.token.logo,
                    'thumbnail': wt.token.thumbnail,
                    'total_amount': Decimal('0'),
                    'total_value': Decimal('0'),
                    'total_value_24h_change': Decimal('0')
                }
            
            # Add this token's balance
            if wt.token_balance_formatted:
                aggregated[key]['total_amount'] += wt.token_balance_formatted
            
            # Add this token's value
            if wt.usd_value:
                aggregated[key]['total_value'] += wt.usd_value
            
            # Add this token's 24h value change
            if wt.usd_value_24h_usd_change:
                aggregated[key]['total_value_24h_change'] += wt.usd_value_24h_usd_change
        
        # Convert to list
        return list(aggregated.values())
    
    @classmethod
    def process_wallet_tokens(cls, wallet, token_data, chain):
        """
        Process token data from Moralis API response
        
        Args:
            wallet: Wallet object
            token_data: Token data from Moralis API
            chain: Blockchain network
            
        Returns:
            int: Number of tokens processed
        """
        try:
            tokens_processed = 0
            
            with transaction.atomic():
                # Clear existing tokens for this wallet to avoid duplicates
                WalletToken.objects.filter(wallet=wallet, chain=chain).delete()
                
                # Process each token in the response
                tokens = token_data.get('result', [])
                logger.info(f"Found {len(tokens)} tokens for wallet {wallet.address} on chain {chain}")
                
                for token_item in tokens:
                    try:
                        # Extract token information with proper field names
                        token_address = token_item.get('token_address')
                        if not token_address:
                            logger.warning(f"Missing token_address in token data: {token_item}")
                            continue
                            
                        # Get or create the token with the correct field mappings
                        token, _ = Token.objects.update_or_create(
                            address=token_address,
                            chain=chain,
                            defaults={
                                'symbol': token_item.get('symbol', ''),
                                'name': token_item.get('name', ''),
                                'logo': token_item.get('logo'),
                                'thumbnail': token_item.get('thumbnail'),
                                'usd_price': token_item.get('usd_price'),
                                'usd_price_24h_percent_change': token_item.get('usd_price_24hr_percent_change'),
                                'usd_price_24h_usd_change': token_item.get('usd_price_24hr_usd_change')
                            }
                        )
                        
                        # Create the wallet-token relationship
                        WalletToken.objects.create(
                            wallet=wallet,
                            token=token,
                            chain=chain,
                            token_balance_formatted=token_item.get('balance_formatted'),
                            usd_value=token_item.get('usd_value'),
                            usd_value_24h_usd_change=token_item.get('usd_value_24hr_usd_change')
                        )
                        
                        tokens_processed += 1
                        
                    except Exception as e:
                        # Log error but continue processing other tokens
                        logger.error(f"Error processing token {token_item.get('token_address')}: {str(e)}")
                
            return tokens_processed
            
        except Exception as e:
            logger.exception(f"Error processing wallet tokens: {str(e)}")
            return 0
    
