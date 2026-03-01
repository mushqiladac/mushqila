"""B2C Referral Models - Placeholder"""
from django.db import models
from .customer import Customer

class ReferralProgram(models.Model):
    name = models.CharField(max_length=200)
    referrer_reward = models.DecimalField(max_digits=10, decimal_places=2)
    referee_reward = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_referral_program'

class CustomerReferral(models.Model):
    referrer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='referrals_made')
    referee = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='referred_by_rel')
    referral_code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_customer_referral'

class AffiliatePartner(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    tracking_code = models.CharField(max_length=50, unique=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_affiliate_partner'

class AffiliateClick(models.Model):
    partner = models.ForeignKey(AffiliatePartner, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    clicked_at = models.DateTimeField(auto_now_add=True)
    converted = models.BooleanField(default=False)
    class Meta:
        db_table = 'b2c_affiliate_click'
