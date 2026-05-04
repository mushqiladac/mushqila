from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import FinanceUser
from ..serializers import (
    FinanceUserSerializer, 
    LoginSerializer, 
    RegisterSerializer,
    PasswordResetSerializer,
    OTPVerifySerializer
)


class AuthViewSet(viewsets.ViewSet):
    """Unified Authentication API Endpoints for Flutter Mobile App"""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """User login endpoint"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, email=email, password=password)
            if user and user.is_active:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                # Update last login
                user.last_login = timezone.now()
                user.last_login_ip = request.META.get('REMOTE_ADDR')
                user.save()
                
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'data': {
                        'user': FinanceUserSerializer(user).data,
                        'tokens': {
                            'access': str(refresh.access_token),
                            'refresh': str(refresh)
                        }
                    }
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid credentials or account inactive'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='create-user', permission_classes=[IsAuthenticated])
    def create_user(self, request):
        """Create new user (Admin/Manager only)"""
        user = request.user
        
        # Check if user has permission to create users
        if user.user_type not in ['admin', 'manager']:
            return Response({
                'success': False,
                'message': 'Permission denied. Only Admin or Manager can create users.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            new_user = serializer.save()
            
            return Response({
                'success': True,
                'message': 'User created successfully',
                'data': {
                    'user': FinanceUserSerializer(new_user).data
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'User creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='refresh-token')
    def refresh_token(self, request):
        """Refresh JWT token endpoint"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'success': False,
                    'message': 'Refresh token required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            refresh = RefreshToken(refresh_token)
            return Response({
                'success': True,
                'data': {
                    'access': str(refresh.access_token)
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """User logout endpoint"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='password-reset-request')
    def password_reset_request(self, request):
        """Request password reset with OTP"""
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = FinanceUser.objects.get(email=email)
                
                # Generate and send OTP
                otp_code = user.generate_otp()
                
                # Send OTP email
                subject = 'Password Reset OTP - Finance App'
                message = f'Your OTP code is: {otp_code}\nThis code will expire in 10 minutes.'
                
                send_mail(
                    subject,
                    message,
                    'noreply@mushqila.com',
                    [email],
                    fail_silently=False,
                )
                
                return Response({
                    'success': True,
                    'message': 'OTP sent to your email',
                    'data': {
                        'alternative_email': user.alternative_email
                    }
                })
            except FinanceUser.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Email not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        """Verify OTP code"""
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                user = FinanceUser.objects.get(email=email)
                
                if user.is_otp_valid(otp_code):
                    user.clear_otp()
                    return Response({
                        'success': True,
                        'message': 'OTP verified successfully',
                        'data': {
                            'reset_token': str(RefreshToken.for_user(user).access_token)
                        }
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Invalid or expired OTP'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except FinanceUser.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Email not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        """Reset password with OTP verification"""
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        reset_token = request.data.get('reset_token')
        
        if not all([email, new_password, reset_token]):
            return Response({
                'success': False,
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = FinanceUser.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            return Response({
                'success': True,
                'message': 'Password reset successful'
            })
        except FinanceUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Email not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Password reset failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='profile')
    def profile(self, request):
        """Get user profile (requires authentication)"""
        if request.user.is_authenticated:
            serializer = FinanceUserSerializer(request.user)
            return Response({
                'success': True,
                'data': serializer.data
            })
        else:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['put'], url_path='update-profile')
    def update_profile(self, request):
        """Update user profile (requires authentication)"""
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = FinanceUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'success': False,
            'message': 'Update failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
