"""
B2C Reviews & Ratings Models
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .customer import Customer


class Review(models.Model):
    """রিভিউ সিস্টেম"""
    
    REVIEW_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('package', 'Package'),
        ('service', 'Service'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    item_id = models.IntegerField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    pros = models.TextField(blank=True)
    cons = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'b2c_review'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.title}"


class ReviewImage(models.Model):
    """রিভিউ ছবি"""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='reviews/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_review_image'
        verbose_name = 'Review Image'
        verbose_name_plural = 'Review Images'
    
    def __str__(self):
        return f"Image for {self.review.title}"


class ReviewResponse(models.Model):
    """রিভিউ রেসপন্স (কোম্পানি থেকে)"""
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name='response'
    )
    response_text = models.TextField()
    responded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )
    responded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'b2c_review_response'
        verbose_name = 'Review Response'
        verbose_name_plural = 'Review Responses'
    
    def __str__(self):
        return f"Response to {self.review.title}"
