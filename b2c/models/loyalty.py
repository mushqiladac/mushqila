"""
B2C Loyalty & Rewards Models
"""
from django.db import models
from django.utils import timezone
from .customer import Customer


class LoyaltyProgram(models.Model):
    """লয়্যালটি প্রোগ্রাম"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    points_per_currency = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Points earned per currency unit spent"
    )
    tier_upgrade_threshold = models.IntegerField(
        help_text="Points needed for tier upgrade"
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'b2c_loyalty_program'
        verbose_name = 'Loyalty Program'
        verbose_name_plural = 'Loyalty Programs'
    
    def __str__(self):
        return self.name


class LoyaltyTransaction(models.Model):
    """পয়েন্ট লেনদেন"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('earn', 'Earn'),
        ('redeem', 'Redeem'),
        ('expire', 'Expire'),
        ('bonus', 'Bonus'),
        ('adjustment', 'Adjustment'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='loyalty_transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES
    )
    points = models.IntegerField()
    booking = models.ForeignKey(
        'flights.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    description = models.TextField()
    expiry_date = models.DateField(null=True, blank=True)
    balance_after = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_loyalty_transaction'
        verbose_name = 'Loyalty Transaction'
        verbose_name_plural = 'Loyalty Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.transaction_type} {self.points} points"


class Reward(models.Model):
    """রিওয়ার্ড/পুরস্কার"""
    
    REWARD_TYPE_CHOICES = [
        ('discount', 'Discount'),
        ('upgrade', 'Upgrade'),
        ('voucher', 'Voucher'),
        ('free_service', 'Free Service'),
        ('cashback', 'Cashback'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    points_required = models.IntegerField()
    reward_type = models.CharField(
        max_length=20,
        choices=REWARD_TYPE_CHOICES
    )
    value = models.DecimalField(max_digits=10, decimal_places=2)
    validity_days = models.IntegerField(
        help_text="Days valid after redemption"
    )
    terms_conditions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(
        null=True,
        blank=True,
        help_text="Leave blank for unlimited"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'b2c_reward'
        verbose_name = 'Reward'
        verbose_name_plural = 'Rewards'
        ordering = ['points_required']
    
    def __str__(self):
        return f"{self.name} ({self.points_required} points)"


class CustomerReward(models.Model):
    """কাস্টমার রিওয়ার্ড"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='rewards'
    )
    reward = models.ForeignKey(
        Reward,
        on_delete=models.CASCADE
    )
    redemption_code = models.CharField(max_length=50, unique=True)
    redeemed_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    booking = models.ForeignKey(
        'flights.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Booking where reward was used"
    )
    
    class Meta:
        db_table = 'b2c_customer_reward'
        verbose_name = 'Customer Reward'
        verbose_name_plural = 'Customer Rewards'
        ordering = ['-redeemed_at']
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.reward.name}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
