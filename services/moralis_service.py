import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class MoralisService:
    """Service for interacting with Moralis API"""
    
    # Define the mapping between user-friendly chain names and Moralis chain identifiers
    CHAIN_MAPPING = {
        'eth': 'eth',
        'bsc': 'bsc', 
        'polygon': 'polygon',
        'avalanche': 'avalanche',
        'fantom': 'fantom',
        'arbitrum': 'arbitrum',
        'optimism': 'optimism'
    }
    
    @classmethod
    def get_wallet_tokens(cls, address, chain=None, exclude_spam=True, exclude_unverified_contracts=True):
        """
        Fetch token list for a wallet from Moralis API
        
        Args:
            address (str): The wallet address
            chain (str, optional): Chain name or ID
            exclude_spam (bool, optional): Whether to exclude spam tokens. Defaults to True.
            exclude_unverified_contracts (bool, optional): Whether to exclude unverified contracts. Defaults to True.
            
        Returns:
            tuple: (success_bool, data_or_error_message)
        """
        try:
            # Prepare the API call
            api_url = f"https://deep-index.moralis.io/api/v2.2/wallets/{address}/tokens"
            headers = {
                'accept': 'application/json',
                'X-API-Key': settings.MORALIS_API_KEY
            }
            
            # Add chain parameter if specified
            params = {
                'exclude_spam': str(exclude_spam).lower(),
                'exclude_unverified_contracts': str(exclude_unverified_contracts).lower()
            }
            
            if chain:
                # Convert chain name to Moralis chain ID if needed
                moralis_chain = cls.CHAIN_MAPPING.get(chain.lower(), chain)
                params['chain'] = moralis_chain
                logger.info(f"Querying Moralis for tokens of wallet {address} on chain {moralis_chain}")
            else:
                logger.info(f"Querying Moralis for tokens of wallet {address} across all chains")
            
            # Make the API call
            response = requests.get(api_url, headers=headers, params=params)
            
            # Log the full response for debugging
            logger.debug(f"Moralis API token response: {response.text}")
            
            # Handle response
            if response.status_code == 200:
                data = response.json()
                return True, data
            else:
                error_msg = f"Moralis API error: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error fetching wallet tokens: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
