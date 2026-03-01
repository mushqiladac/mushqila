"""
B2C Admin Configuration
"""
from django.contrib import admin
from .models import (
    Customer, CustomerProfile, TravelCompanion,
    LoyaltyProgram, LoyaltyTransaction, Reward, CustomerReward,
    Wishlist, WishlistItem, FavoriteDestination, FavoriteAirline,
    Review, ReviewImage, ReviewResponse,
    PriceAlert, TravelAlert, NewsletterSubscription,
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'customer_type', 'loyalty_tier', 'loyalty_points', 'total_bookings', 'created_at']
    list_filter = ['customer_type', 'loyalty_tier', 'is_verified']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['customer', 'date_of_birth', 'gender', 'nationality']
    search_fields = ['customer__user__email', 'passport_number']


@admin.register(TravelCompanion)
class TravelCompanionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'name', 'relationship', 'is_frequent']
    list_filter = ['relationship', 'is_frequent']
    search_fields = ['name', 'customer__user__email']


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_per_currency', 'is_active', 'start_date']
    list_filter = ['is_active']


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'transaction_type', 'points', 'balance_after', 'created_at']
    list_filter = ['transaction_type']
    search_fields = ['customer__user__email']
    readonly_fields = ['created_at']


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ['name', 'reward_type', 'points_required', 'value', 'is_active']
    list_filter = ['reward_type', 'is_active']


@admin.register(CustomerReward)
class CustomerRewardAdmin(admin.ModelAdmin):
    list_display = ['customer', 'reward', 'status', 'redeemed_at', 'expires_at']
    list_filter = ['status']
    search_fields = ['customer__user__email', 'redemption_code']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['customer', 'name', 'is_default', 'created_at']
    search_fields = ['customer__user__email', 'name']


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'item_type', 'item_id', 'notify_on_discount']
    list_filter = ['item_type', 'notify_on_discount']


@admin.register(FavoriteDestination)
class FavoriteDestinationAdmin(admin.ModelAdmin):
    list_display = ['customer', 'city', 'visit_count', 'last_visited']
    search_fields = ['customer__user__email', 'city__name']


@admin.register(FavoriteAirline)
class FavoriteAirlineAdmin(admin.ModelAdmin):
    list_display = ['customer', 'airline', 'preference_score']
    search_fields = ['customer__user__email', 'airline__name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer', 'review_type', 'rating', 'title', 'status', 'created_at']
    list_filter = ['review_type', 'status', 'rating']
    search_fields = ['customer__user__email', 'title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['review', 'caption', 'created_at']


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ['review', 'responded_by', 'responded_at']
    readonly_fields = ['responded_at']


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ['customer', 'route', 'target_price', 'is_active', 'created_at']
    list_filter = ['is_active', 'alert_type']
    search_fields = ['customer__user__email', 'route']


@admin.register(TravelAlert)
class TravelAlertAdmin(admin.ModelAdmin):
    list_display = ['customer', 'alert_type', 'alert_date', 'is_sent']
    list_filter = ['alert_type', 'is_sent']
    search_fields = ['customer__user__email']


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'subscription_type', 'frequency', 'is_active']
    list_filter = ['subscription_type', 'frequency', 'is_active']
    search_fields = ['customer__user__email']
