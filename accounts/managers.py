"""
Custom managers for B2B Travel Platform - Saudi Arabia
"""

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.db import models


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('status', 'active')
        extra_fields.setdefault('kyc_verified', True)
        extra_fields.setdefault('email_verified', True)
        extra_fields.setdefault('phone_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)
    
    def get_active_users(self):
        """Get all active users"""
        return self.filter(status='active', is_active=True)
    
    def get_saudi_users(self):
        """Get users from Saudi Arabia"""
        return self.filter(nationality='Saudi Arabia')
    
    def get_agents(self):
        """Get all agent type users"""
        return self.filter(
            user_type__in=['agent', 'super_agent', 'sub_agent']
        )
    
    def get_kyc_verified(self):
        """Get all KYC verified users"""
        return self.filter(kyc_verified=True)


class SaudiCityManager(models.Manager):
    """Custom manager for SaudiCity model"""
    
    def get_major_cities(self):
        """Get all major cities in Saudi Arabia"""
        return self.filter(is_major_city=True, is_active=True)
    
    def get_hajj_cities(self):
        """Get Hajj cities (Makkah, Madinah)"""
        return self.filter(is_hajj_city=True, is_active=True)
    
    def get_umrah_cities(self):
        """Get Umrah cities"""
        return self.filter(is_umrah_city=True, is_active=True)
    
    def get_by_region(self, region_code):
        """Get cities by region code"""
        return self.filter(region__region_code=region_code, is_active=True)
    
    def get_active_cities(self):
        """Get all active cities"""
        return self.filter(is_active=True)


class TransactionManager(models.Manager):
    """Custom manager for Transaction model"""
    
    def get_successful_transactions(self):
        """Get all successful transactions"""
        return self.filter(status='completed')
    
    def get_pending_transactions(self):
        """Get all pending transactions"""
        return self.filter(status='pending')
    
    def get_transactions_by_type(self, transaction_type):
        """Get transactions by type"""
        return self.filter(transaction_type=transaction_type)
    
    def get_today_transactions(self):
        """Get today's transactions"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.filter(created_at__date=today)
    
    def get_user_transactions(self, user):
        """Get all transactions for a user"""
        return self.filter(user=user).order_by('-created_at')