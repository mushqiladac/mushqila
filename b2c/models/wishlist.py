"""
B2C Wishlist & Favorites Models
"""
from django.db import models
from .customer import Customer


class Wishlist(models.Model):
    """উইশলিস্ট"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    name = models.CharField(max_length=200, default="My Wishlist")
    is_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'b2c_wishlist'
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.name}"


class WishlistItem(models.Model):
    """উইশলিস্ট আইটেম"""
    
    ITEM_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('package', 'Package'),
        ('destination', 'Destination'),
    ]
    
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.IntegerField()
    notes = models.TextField(blank=True)
    price_alert = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Alert when price drops below this"
    )
    notify_on_discount = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_wishlist_item'
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ['wishlist', 'item_type', 'item_id']
    
    def __str__(self):
        return f"{self.item_type} #{self.item_id}"


class FavoriteDestination(models.Model):
    """প্রিয় গন্তব্য"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='favorite_destinations'
    )
    city = models.ForeignKey(
        'accounts.SaudiCity',
        on_delete=models.CASCADE
    )
    visit_count = models.IntegerField(default=0)
    last_visited = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_favorite_destination'
        verbose_name = 'Favorite Destination'
        verbose_name_plural = 'Favorite Destinations'
        unique_together = ['customer', 'city']
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.city.name}"


class FavoriteAirline(models.Model):
    """প্রিয় এয়ারলাইন"""
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='favorite_airlines'
    )
    airline = models.ForeignKey(
        'flights.Airline',
        on_delete=models.CASCADE
    )
    preference_score = models.IntegerField(
        default=0,
        help_text="Higher score = more preferred"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_favorite_airline'
        verbose_name = 'Favorite Airline'
        verbose_name_plural = 'Favorite Airlines'
        unique_together = ['customer', 'airline']
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.airline.name}"
