"""B2C Wallet Models - Placeholder"""
from django.db import models
from .customer import Customer

class CustomerWallet(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='SAR')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_customer_wallet'

class WalletTransaction(models.Model):
    wallet = models.ForeignKey(CustomerWallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_wallet_transaction'

class SavedPaymentMethod(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    method_type = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_saved_payment_method'
