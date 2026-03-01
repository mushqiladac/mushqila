"""
B2C Customer Models
"""
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


class Customer(models.Model):
    """B2C Customer - সাধারণ ভ্রমণকারী"""
    
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('family', 'Family'),
        ('corporate', 'Corporate'),
    ]
    
    LOYALTY_TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='b2c_customer'
    )
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default='individual'
    )
    loyalty_tier = models.CharField(
        max_length=20,
        choices=LOYALTY_TIER_CHOICES,
        default='bronze'
    )
    loyalty_points = models.IntegerField(default=0)
    total_bookings = models.IntegerField(default=0)
    lifetime_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    preferred_language = models.CharField(
        max_length=10,
        default='en',
        choices=[
            ('en', 'English'),
            ('ar', 'Arabic'),
            ('bn', 'Bengali'),
            ('ur', 'Urdu'),
        ]
    )
    preferred_currency = models.CharField(
        max_length=3,
        default='SAR'
    )
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'b2c_customer'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.loyalty_tier})"


class CustomerProfile(models.Model):
    """বিস্তারিত প্রোফাইল"""
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True
    )
    nationality = models.CharField(max_length=100, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    passport_country = models.CharField(max_length=100, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Preferences
    dietary_preferences = models.JSONField(default=dict, blank=True)
    special_assistance = models.JSONField(default=dict, blank=True)
    seat_preference = models.CharField(
        max_length=20,
        choices=[
            ('window', 'Window'),
            ('aisle', 'Aisle'),
            ('middle', 'Middle'),
            ('no_preference', 'No Preference'),
        ],
        default='no_preference'
    )
    meal_preference = models.CharField(max_length=50, blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'b2c_customer_profile'
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'
    
    def __str__(self):
        return f"Profile of {self.customer.user.get_full_name()}"


class TravelCompanion(models.Model):
    """ভ্রমণ সঙ্গী (পরিবার/বন্ধু)"""
    
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('friend', 'Friend'),
        ('colleague', 'Colleague'),
        ('other', 'Other'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='companions'
    )
    name = models.CharField(max_length=200)
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=CustomerProfile.GENDER_CHOICES,
        blank=True
    )
    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    is_frequent = models.BooleanField(
        default=False,
        help_text="Frequently travels with this customer"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'b2c_travel_companion'
        verbose_name = 'Travel Companion'
        verbose_name_plural = 'Travel Companions'
        ordering = ['-is_frequent', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.relationship})"
