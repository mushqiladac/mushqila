# accounts/api_serializers.py
"""
B2B Travel Platform API Serializers for Flutter Mobile App
Complete unified API for agents, bookings, and business operations
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    User, UserProfile, Transaction, Notification, SaudiCity, SaudiRegion,
    Document, AgentHierarchy, CreditRequest, FlightBooking, HotelBooking,
    HajjPackage, UmrahPackage, ServiceSupplier
)
from .models.b2b import (
    BusinessUnit, PermissionGroup, APIKey, BusinessRule,
    DashboardWidget, SystemConfiguration, AuditLog
)
from decimal import Decimal

User = get_user_model()


# ============================================================================
# User & Authentication Serializers
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    company_name = serializers.SerializerMethodField()
    available_credit = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'user_type', 'status', 'company_name', 'company_name_ar',
            'company_name_en', 'company_registration', 'vat_number',
            'credit_limit', 'current_balance', 'wallet_balance',
            'commission_rate', 'available_credit', 'referral_code',
            'email_verified', 'phone_verified', 'kyc_verified',
            'created_at', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at', 'referral_code']
    
    def get_company_name(self, obj):
        return obj.get_company_name('en')
    
    def get_available_credit(self, obj):
        return float(obj.available_credit())


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = UserProfile
        fields = [
            'business_type', 'years_in_business', 'bank_name_en',
            'bank_name_ar', 'account_number', 'iban', 'total_bookings',
            'total_sales', 'total_commission', 'hajj_bookings',
            'umrah_bookings', 'language', 'timezone'
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer with profile"""
    profile = UserProfileSerializer(read_only=True)
    city_name = serializers.CharField(source='city.name_en', read_only=True)
    region_name = serializers.CharField(source='city.region.name_en', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'user_type', 'status', 'company_name_en', 'company_name_ar',
            'company_registration', 'vat_number', 'credit_limit',
            'current_balance', 'wallet_balance', 'commission_rate',
            'referral_code', 'referred_by', 'scta_license', 'hajj_license',
            'iata_number', 'email_verified', 'phone_verified', 'kyc_verified',
            'city', 'city_name', 'region_name', 'address_en', 'address_ar',
            'profile', 'created_at', 'updated_at', 'last_activity'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RegisterSerializer(serializers.Serializer):
    """Registration serializer"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=15)
    company_name_en = serializers.CharField(max_length=255)
    company_name_ar = serializers.CharField(max_length=255, required=False)
    company_registration = serializers.CharField(max_length=50, required=False)
    vat_number = serializers.CharField(max_length=15, required=False)
    user_type = serializers.ChoiceField(choices=['agent', 'sub_agent', 'corporate'])
    referral_code = serializers.CharField(max_length=20, required=False)
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Change password serializer"""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data


# ============================================================================
# Transaction & Financial Serializers
# ============================================================================

class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'user', 'user_email', 'user_name',
            'transaction_type', 'amount', 'currency', 'status',
            'description', 'description_ar', 'reference',
            'balance_before', 'balance_after', 'vat_amount',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()


class CreditRequestSerializer(serializers.ModelSerializer):
    """Credit request serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    increase_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = CreditRequest
        fields = [
            'id', 'user', 'user_email', 'current_limit',
            'requested_limit', 'increase_amount', 'purpose',
            'status', 'review_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_limit', 'created_at', 'updated_at']
    
    def get_increase_amount(self, obj):
        return float(obj.get_increase_amount())


# ============================================================================
# Booking Serializers
# ============================================================================

class ServiceSupplierSerializer(serializers.ModelSerializer):
    """Service supplier serializer"""
    
    class Meta:
        model = ServiceSupplier
        fields = [
            'id', 'name', 'name_ar', 'supplier_type', 'code',
            'commission_rate', 'is_active'
        ]


class FlightBookingListSerializer(serializers.ModelSerializer):
    """Flight booking list serializer (minimal data)"""
    agent_name = serializers.SerializerMethodField()
    airline_name = serializers.CharField(source='airline.name', read_only=True)
    route = serializers.SerializerMethodField()
    
    class Meta:
        model = FlightBooking
        fields = [
            'id', 'booking_id', 'agent', 'agent_name', 'passenger_name',
            'airline_name', 'flight_number', 'route', 'departure_date',
            'arrival_date', 'travel_type', 'total_amount',
            'commission_amount', 'status', 'pnr', 'created_at'
        ]
        read_only_fields = ['id', 'booking_id', 'created_at']
    
    def get_agent_name(self, obj):
        return obj.agent.get_full_name()
    
    def get_route(self, obj):
        return f"{obj.departure_city} → {obj.arrival_city}"


class FlightBookingDetailSerializer(serializers.ModelSerializer):
    """Flight booking detail serializer (full data)"""
    agent = UserSerializer(read_only=True)
    airline = ServiceSupplierSerializer(read_only=True)
    
    class Meta:
        model = FlightBooking
        fields = '__all__'
        read_only_fields = ['id', 'booking_id', 'created_at', 'updated_at']


class FlightBookingCreateSerializer(serializers.ModelSerializer):
    """Flight booking creation serializer"""
    
    class Meta:
        model = FlightBooking
        fields = [
            'passenger_name', 'passenger_name_ar', 'passenger_email',
            'passenger_phone', 'airline', 'flight_number',
            'departure_city', 'arrival_city', 'departure_airport',
            'arrival_airport', 'departure_date', 'arrival_date',
            'travel_type', 'booking_class', 'base_fare', 'tax',
            'vat', 'booking_notes'
        ]


class HotelBookingListSerializer(serializers.ModelSerializer):
    """Hotel booking list serializer"""
    agent_name = serializers.SerializerMethodField()
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    
    class Meta:
        model = HotelBooking
        fields = [
            'id', 'booking_id', 'agent', 'agent_name', 'guest_name',
            'hotel_name', 'check_in', 'check_out', 'nights',
            'rooms', 'total_amount', 'commission_amount',
            'status', 'confirmation_number', 'created_at'
        ]
        read_only_fields = ['id', 'booking_id', 'created_at']
    
    def get_agent_name(self, obj):
        return obj.agent.get_full_name()


class HotelBookingDetailSerializer(serializers.ModelSerializer):
    """Hotel booking detail serializer"""
    agent = UserSerializer(read_only=True)
    hotel = ServiceSupplierSerializer(read_only=True)
    
    class Meta:
        model = HotelBooking
        fields = '__all__'
        read_only_fields = ['id', 'booking_id', 'created_at', 'updated_at']


class HotelBookingCreateSerializer(serializers.ModelSerializer):
    """Hotel booking creation serializer"""
    
    class Meta:
        model = HotelBooking
        fields = [
            'hotel', 'guest_name', 'guest_email', 'guest_phone',
            'check_in', 'check_out', 'rooms', 'adults', 'children',
            'room_rate', 'booking_notes'
        ]


# ============================================================================
# Hajj & Umrah Serializers
# ============================================================================

class HajjPackageSerializer(serializers.ModelSerializer):
    """Hajj package serializer"""
    available_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = HajjPackage
        fields = [
            'id', 'package_code', 'name', 'name_ar', 'description',
            'description_ar', 'duration_days', 'hajj_year',
            'makkah_hotel', 'makkah_hotel_distance', 'madinah_hotel',
            'madinah_hotel_distance', 'flight_included',
            'transport_included', 'base_price', 'commission_rate',
            'available_slots', 'total_slots', 'available_percentage',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'package_code', 'created_at']
    
    def get_available_percentage(self, obj):
        if obj.total_slots > 0:
            return round((obj.available_slots / obj.total_slots) * 100, 2)
        return 0


class UmrahPackageSerializer(serializers.ModelSerializer):
    """Umrah package serializer"""
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = UmrahPackage
        fields = [
            'id', 'package_code', 'name', 'name_ar', 'package_type',
            'duration_days', 'validity_from', 'validity_to', 'is_valid',
            'makkah_hotel', 'makkah_nights', 'madinah_hotel',
            'madinah_nights', 'flight_included', 'visa_included',
            'transport_included', 'ziyarat_included', 'base_price',
            'commission_rate', 'created_at'
        ]
        read_only_fields = ['id', 'package_code', 'created_at']
    
    def get_is_valid(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        return obj.validity_from <= today <= obj.validity_to


# ============================================================================
# Notification & Document Serializers
# ============================================================================

class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'title_ar',
            'message', 'message_ar', 'is_read', 'action_url',
            'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer"""
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'document_number', 'document_file',
            'front_image', 'back_image', 'issue_date', 'expiry_date',
            'status', 'verification_notes', 'verified_at', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'verification_notes', 'verified_at', 'created_at']


# ============================================================================
# Dashboard & Statistics Serializers
# ============================================================================

class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics serializer"""
    total_bookings = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_commission = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    wallet_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    available_credit = serializers.DecimalField(max_digits=15, decimal_places=2)
    unread_notifications = serializers.IntegerField()
    hajj_bookings = serializers.IntegerField()
    umrah_bookings = serializers.IntegerField()
    flight_bookings = serializers.IntegerField()
    hotel_bookings = serializers.IntegerField()


class AgentHierarchySerializer(serializers.ModelSerializer):
    """Agent hierarchy serializer"""
    parent_name = serializers.SerializerMethodField()
    child_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentHierarchy
        fields = [
            'id', 'parent_agent', 'parent_name', 'child_agent',
            'child_name', 'hierarchy_level', 'commission_share',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_parent_name(self, obj):
        return obj.parent_agent.get_full_name()
    
    def get_child_name(self, obj):
        return obj.child_agent.get_full_name()


# ============================================================================
# Location Serializers
# ============================================================================

class SaudiCitySerializer(serializers.ModelSerializer):
    """Saudi city serializer"""
    region_name = serializers.CharField(source='region.name_en', read_only=True)
    
    class Meta:
        model = SaudiCity
        fields = [
            'id', 'name_en', 'name_ar', 'region', 'region_name',
            'postal_code', 'is_major_city', 'is_hajj_city',
            'is_umrah_city', 'latitude', 'longitude'
        ]


class SaudiRegionSerializer(serializers.ModelSerializer):
    """Saudi region serializer"""
    
    class Meta:
        model = SaudiRegion
        fields = [
            'id', 'region_code', 'name_en', 'name_ar',
            'capital_en', 'capital_ar', 'is_active'
        ]
