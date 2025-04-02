from django.db import models
from wallets.models import Wallet

class Token(models.Model):
    """
    Model to store token information
    """
    address = models.CharField(max_length=255, db_index=True)
    chain = models.CharField(max_length=50, db_index=True)
    symbol = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    logo = models.URLField(max_length=500, null=True, blank=True)
    thumbnail = models.URLField(max_length=500, null=True, blank=True)
    usd_price = models.DecimalField(max_digits=30, decimal_places=18, null=True, blank=True)
    usd_price_24h_percent_change = models.DecimalField(max_digits=30, decimal_places=18, null=True, blank=True)
    usd_price_24h_usd_change = models.DecimalField(max_digits=30, decimal_places=18, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # ensure each token is unique per chain
        unique_together = ('address', 'chain')

    def __str__(self):
        return f"{self.chain} {self.symbol} ({self.address[:5]}...{self.address[-5:]})"

class WalletToken(models.Model):
    """
    Association between wallet and tokens
    """
    # Foreign key relationships
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    token = models.ForeignKey(Token, on_delete=models.CASCADE)

    chain = models.CharField(max_length=50)

    # Balance information
    token_balance_formatted = models.DecimalField(max_digits=30, decimal_places=18, null=True, blank=True)
    usd_value = models.DecimalField(max_digits=30, decimal_places=18, null=True, blank=True)
    usd_value_24h_usd_change = models.DecimalField(max_digits=30, decimal_places=18, null=True, blank= True)

    class Meta:
        # ensure unique wallet, chain and token entry is unique
        unique_together = ('wallet', 'token', 'chain')

    def __str__(self):
        return f"{self.wallet.chain} ({self.wallet.address[:5]}...{self.wallet.address[-5:]}) ({self.token.address[:5]}...{self.token.address[-5:]})"
