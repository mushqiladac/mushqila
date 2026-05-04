from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from ..models import FinanceUser, FinanceUserProfile


class FinanceUserSerializer(serializers.ModelSerializer):
    """Serializer for Finance User model"""
    
    profile = serializers.SerializerMethodField()
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FinanceUser
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'phone',
            'alternative_email', 'user_type', 'user_type_display', 'status', 'status_display',
            'credit_limit', 'current_balance', 'total_sales',
            'email_verified', 'phone_verified',
            'last_login', 'created_at', 'updated_at', 'profile'
        ]
        read_only_fields = [
            'id', 'username', 'credit_limit', 'current_balance', 'total_sales',
            'email_verified', 'phone_verified', 'last_login', 'created_at', 'updated_at'
        ]
    
    def get_profile(self, obj):
        """Get user profile data"""
        try:
            profile = obj.finance_profile
            return {
                'company_name': profile.company_name,
                'company_registration': profile.company_registration,
                'bank_name': profile.bank_name,
                'account_number': profile.account_number,
                'iban': profile.iban,
                'language': profile.language,
                'timezone': profile.timezone,
                'total_tickets_sold': profile.total_tickets_sold,
                'total_commission': float(profile.total_commission)
            }
        except FinanceUserProfile.DoesNotExist:
            return None
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        user = self.context['request'].user if 'request' in self.context else None
        if user and user.email == value:
            return value
        
        if FinanceUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_phone(self, value):
        """Validate phone uniqueness"""
        if not value:
            return value
            
        user = self.context['request'].user if 'request' in self.context else None
        if user and user.phone == value:
            return value
        
        if FinanceUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    
    def validate(self, attrs):
        """Validate login credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                email=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            
            if not user.is_active:
                raise serializers.ValidationError("Account is inactive")
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Email and password are required")


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = FinanceUser
        fields = [
            'email', 'first_name', 'last_name', 'phone', 'alternative_email',
            'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validate registration data"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if FinanceUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate_phone(self, value):
        """Validate phone uniqueness"""
        if value and FinanceUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists")
        return value
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = FinanceUser.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create user profile
        FinanceUserProfile.objects.create(user=user)
        
        return user


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email exists"""
        if not FinanceUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email not found")
        return value


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    
    def validate(self, attrs):
        """Validate OTP"""
        email = attrs.get('email')
        otp_code = attrs.get('otp_code')
        
        try:
            user = FinanceUser.objects.get(email=email)
            if not user.is_otp_valid(otp_code):
                raise serializers.ValidationError("Invalid or expired OTP")
        except FinanceUser.DoesNotExist:
            raise serializers.ValidationError("Email not found")
        
        return attrs


class FinanceUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for Finance User Profile"""
    
    class Meta:
        model = FinanceUserProfile
        fields = [
            'company_name', 'company_registration', 'bank_name', 
            'account_number', 'iban', 'language', 'timezone'
        ]
