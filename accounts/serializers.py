# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserProfile, Transaction, Notification, Document,
    LoginHistory, AgentHierarchy, CreditRequest, SMSCode,
    IPWhitelist, ComplianceCheck, Payment, Invoice, Refund,
    CommissionTransaction, ServiceSupplier, FlightBooking,
    HotelBooking, HajjPackage, UmrahPackage, SaudiRegion,
    SaudiCity, UserActivityLog
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    full_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name',
            'user_type', 'status', 'company_name_en', 'company_name_ar',
            'company_registration', 'vat_number', 'credit_limit',
            'current_balance', 'wallet_balance', 'commission_rate',
            'kyc_verified', 'email_verified', 'phone_verified',
            'city', 'city_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_city_name(self, obj):
        if obj.city:
            return obj.city.name_en
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'business_type', 'years_in_business',
            'bank_name_en', 'account_number', 'iban', 'total_bookings',
            'total_sales', 'total_commission', 'hajj_bookings',
            'umrah_bookings', 'language', 'timezone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'user', 'user_email', 'transaction_type',
            'amount', 'currency', 'status', 'description', 'description_ar',
            'reference', 'balance_before', 'balance_after', 'vat_amount',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'user', 'user_email', 'amount', 'vat_amount',
            'total_amount', 'payment_method', 'status', 'reference_number',
            'transaction_id', 'bank_name', 'cheque_number', 'description',
            'description_ar', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'completed_at']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'user', 'user_email', 'subtotal',
            'vat_amount', 'total_amount', 'paid_amount', 'status',
            'issue_date', 'due_date', 'payment_date', 'notes', 'notes_ar',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refund"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Refund
        fields = [
            'id', 'refund_id', 'user', 'user_email', 'refund_amount',
            'refund_method', 'status', 'reason', 'admin_notes',
            'requested_at', 'approved_at', 'processed_at'
        ]
        read_only_fields = ['requested_at', 'approved_at', 'processed_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    document_type_display = serializers.ReadOnlyField(source='get_document_type_display')
    status_display = serializers.ReadOnlyField(source='get_status_display')
    
    class Meta:
        model = Document
        fields = [
            'id', 'user', 'user_email', 'document_type', 'document_type_display',
            'document_number', 'document_file', 'front_image', 'back_image',
            'issue_date', 'expiry_date', 'status', 'status_display',
            'verification_notes', 'verified_by', 'verified_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'verified_at']


class FlightBookingSerializer(serializers.ModelSerializer):
    """Serializer for FlightBooking"""
    
    agent_email = serializers.ReadOnlyField(source='agent.email')
    airline_name = serializers.ReadOnlyField(source='airline.name')
    
    class Meta:
        model = FlightBooking
        fields = [
            'id', 'booking_id', 'agent', 'agent_email', 'passenger_name',
            'passenger_name_ar', 'passenger_email', 'passenger_phone',
            'airline', 'airline_name', 'flight_number', 'departure_city',
            'arrival_city', 'departure_airport', 'arrival_airport',
            'departure_date', 'arrival_date', 'travel_type', 'booking_class',
            'base_fare', 'tax', 'vat', 'total_amount', 'commission_amount',
            'status', 'pnr', 'ticket_number', 'booking_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class HotelBookingSerializer(serializers.ModelSerializer):
    """Serializer for HotelBooking"""
    
    agent_email = serializers.ReadOnlyField(source='agent.email')
    hotel_name = serializers.ReadOnlyField(source='hotel.name')
    
    class Meta:
        model = HotelBooking
        fields = [
            'id', 'booking_id', 'agent', 'agent_email', 'guest_name',
            'guest_email', 'guest_phone', 'hotel', 'hotel_name',
            'check_in', 'check_out', 'nights', 'rooms', 'adults',
            'children', 'room_rate', 'total_amount', 'commission_amount',
            'status', 'confirmation_number', 'booking_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class HajjPackageSerializer(serializers.ModelSerializer):
    """Serializer for HajjPackage"""
    
    class Meta:
        model = HajjPackage
        fields = [
            'id', 'package_code', 'name', 'name_ar', 'description',
            'description_ar', 'duration_days', 'hajj_year',
            'makkah_hotel', 'makkah_hotel_distance', 'madinah_hotel',
            'madinah_hotel_distance', 'flight_included',
            'transport_included', 'base_price', 'commission_rate',
            'available_slots', 'total_slots', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UmrahPackageSerializer(serializers.ModelSerializer):
    """Serializer for UmrahPackage"""
    
    class Meta:
        model = UmrahPackage
        fields = [
            'id', 'package_code', 'name', 'name_ar', 'package_type',
            'duration_days', 'validity_from', 'validity_to',
            'makkah_hotel', 'makkah_nights', 'madinah_hotel',
            'madinah_nights', 'flight_included', 'visa_included',
            'transport_included', 'ziyarat_included', 'base_price',
            'commission_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SaudiRegionSerializer(serializers.ModelSerializer):
    """Serializer for SaudiRegion"""
    
    class Meta:
        model = SaudiRegion
        fields = [
            'id', 'region_code', 'name_ar', 'name_en',
            'capital_ar', 'capital_en', 'is_active'
        ]


class SaudiCitySerializer(serializers.ModelSerializer):
    """Serializer for SaudiCity"""
    
    region_name = serializers.ReadOnlyField(source='region.name_en')
    
    class Meta:
        model = SaudiCity
        fields = [
            'id', 'region', 'region_name', 'name_ar', 'name_en',
            'postal_code', 'is_major_city', 'is_hajj_city',
            'is_umrah_city', 'is_active', 'latitude', 'longitude'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_email', 'notification_type', 'title',
            'title_ar', 'message', 'message_ar', 'is_read', 'action_url',
            'created_at', 'read_at'
        ]
        read_only_fields = ['created_at', 'read_at']


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for LoginHistory"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = LoginHistory
        fields = [
            'id', 'user', 'user_email', 'ip_address', 'user_agent',
            'location', 'country_code', 'success', 'failure_reason',
            'created_at'
        ]
        read_only_fields = ['created_at']


class AgentHierarchySerializer(serializers.ModelSerializer):
    """Serializer for AgentHierarchy"""
    
    parent_agent_email = serializers.ReadOnlyField(source='parent_agent.email')
    child_agent_email = serializers.ReadOnlyField(source='child_agent.email')
    
    class Meta:
        model = AgentHierarchy
        fields = [
            'id', 'parent_agent', 'parent_agent_email', 'child_agent',
            'child_agent_email', 'hierarchy_level', 'commission_share',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CreditRequestSerializer(serializers.ModelSerializer):
    """Serializer for CreditRequest"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = CreditRequest
        fields = [
            'id', 'user', 'user_email', 'current_limit', 'requested_limit',
            'purpose', 'status', 'review_notes', 'approved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'approved_at']


class SMSCodeSerializer(serializers.ModelSerializer):
    """Serializer for SMSCode"""
    
    class Meta:
        model = SMSCode
        fields = [
            'id', 'phone', 'code', 'purpose', 'is_used', 'expires_at',
            'created_at'
        ]
        read_only_fields = ['created_at']


class IPWhitelistSerializer(serializers.ModelSerializer):
    """Serializer for IPWhitelist"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = IPWhitelist
        fields = [
            'id', 'user', 'user_email', 'ip_address', 'description',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ComplianceCheckSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceCheck"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = ComplianceCheck
        fields = [
            'id', 'user', 'user_email', 'check_type', 'status', 'score',
            'details', 'notes', 'performed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'performed_at']


class CommissionTransactionSerializer(serializers.ModelSerializer):
    """Serializer for CommissionTransaction"""
    
    agent_email = serializers.ReadOnlyField(source='agent.email')
    
    class Meta:
        model = CommissionTransaction
        fields = [
            'id', 'transaction_id', 'agent', 'agent_email', 'amount',
            'commission_rate', 'status', 'payment_date', 'remarks',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ServiceSupplierSerializer(serializers.ModelSerializer):
    """Serializer for ServiceSupplier"""
    
    class Meta:
        model = ServiceSupplier
        fields = [
            'id', 'name', 'name_ar', 'supplier_type', 'code',
            'commission_rate', 'contact_person', 'contact_email',
            'contact_phone', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for UserActivityLog"""
    
    user_email = serializers.ReadOnlyField(source='user.email')
    
    class Meta:
        model = UserActivityLog
        fields = [
            'id', 'user', 'user_email', 'activity_type', 'description',
            'ip_address', 'user_agent', 'metadata', 'created_at'
        ]
        read_only_fields = ['created_at']


# Registration and Authentication Serializers

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [
            'email', 'phone', 'first_name', 'last_name',
            'company_name_en', 'company_registration',
            'user_type', 'password', 'password_confirm'
        ]
    
    def validate(self, data):
        """Validate registration data"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Validate Saudi phone format
        phone = data.get('phone', '')
        if not phone.startswith('+9665'):
            raise serializers.ValidationError({
                'phone': 'Phone number must be in Saudi format: +9665XXXXXXXX'
            })
        
        return data
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    remember_me = serializers.BooleanField(default=False)


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset"""
    
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    token = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})
    password_confirm = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    current_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'})
    confirm_password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'New passwords do not match.'
            })
        return data


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    total_users = serializers.IntegerField(default=0)
    new_users_today = serializers.IntegerField(default=0)
    total_bookings = serializers.IntegerField(default=0)
    bookings_today = serializers.IntegerField(default=0)
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    wallet_balances = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    pending_kyc = serializers.IntegerField(default=0)
    pending_payments = serializers.IntegerField(default=0)
    pending_withdrawals = serializers.IntegerField(default=0)