"""
B2C Price Alerts & Notifications Models
"""
from django.db import models
from .customer import Customer


class PriceAlert(models.Model):
    """প্রাইস এলার্ট"""
    ALERT_TYPE_CHOICES = [
        ('below', 'Below Target'),
        ('percentage', 'Percentage Drop'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='price_alerts')
    route = models.CharField(max_length=100, help_text="e.g., DAC-JED")
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_price_alert'
        verbose_name = 'Price Alert'
        verbose_name_plural = 'Price Alerts'
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.route}"


class TravelAlert(models.Model):
    """ভ্রমণ এলার্ট"""
    ALERT_TYPE_CHOICES = [
        ('visa_expiry', 'Visa Expiry'),
        ('passport_expiry', 'Passport Expiry'),
        ('booking_reminder', 'Booking Reminder'),
        ('check_in', 'Check-in Reminder'),
        ('flight_status', 'Flight Status'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='travel_alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    alert_date = models.DateTimeField()
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_travel_alert'
        verbose_name = 'Travel Alert'
        verbose_name_plural = 'Travel Alerts'
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.alert_type}"


class NewsletterSubscription(models.Model):
    """নিউজলেটার সাবস্ক্রিপশন"""
    SUBSCRIPTION_TYPE_CHOICES = [
        ('deals', 'Deals & Offers'),
        ('travel_tips', 'Travel Tips'),
        ('destination_guides', 'Destination Guides'),
        ('all', 'All Updates'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='newsletter_subscriptions')
    subscription_type = models.CharField(max_length=30, choices=SUBSCRIPTION_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_newsletter_subscription'
        verbose_name = 'Newsletter Subscription'
        verbose_name_plural = 'Newsletter Subscriptions'
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.subscription_type}"
