"""
B2C Signals
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Customer, CustomerWallet

User = get_user_model()


@receiver(post_save, sender=Customer)
def create_customer_wallet(sender, instance, created, **kwargs):
    """Create wallet when customer is created"""
    if created:
        CustomerWallet.objects.create(customer=instance)


@receiver(post_save, sender=Customer)
def update_loyalty_tier(sender, instance, created, **kwargs):
    """Update loyalty tier based on points"""
    if not created:
        points = instance.loyalty_points
        
        if points >= 10000:
            tier = 'platinum'
        elif points >= 5000:
            tier = 'gold'
        elif points >= 2000:
            tier = 'silver'
        else:
            tier = 'bronze'
        
        if instance.loyalty_tier != tier:
            instance.loyalty_tier = tier
            instance.save(update_fields=['loyalty_tier'])
