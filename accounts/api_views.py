# accounts/api_views.py
"""
B2B Travel Platform API Views for Flutter Mobile App
Complete unified API for agents, bookings, and business operations
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal

from .models import (
    User, UserProfile, Transaction, Notification, SaudiCity, SaudiRegion,
    Document, AgentHierarchy, CreditRequest, FlightBooking, HotelBooking,
    HajjPackage, UmrahPackage, ServiceSupplier
)
from .api_serializers import (
    UserSerializer, UserDetailSerializer, UserProfileSerializer,
    RegisterSerializer, LoginSerializer, ChangePasswordSerializer,
    TransactionSerializer, CreditRequestSerializer,
    FlightBookingListSerializer, FlightBookingDetailSerializer,
    FlightBookingCreateSerializer, HotelBookingListSerializer,
    HotelBookingDetailSerializer, HotelBookingCreateSerializer,
    HajjPackageSerializer, UmrahPackageSerializer,
    NotificationSerializer, DocumentSerializer,
    DashboardStatsSerializer, AgentHierarchySerializer,
    SaudiCitySerializer, SaudiRegionSerializer, ServiceSupplierSerializer
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners or admins"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.user_type == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'agent'):
            return obj.agent == request.user
        return obj == request.user


# ============================================================================
# Authentication Views
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """Register new user"""
    serializer = RegisterSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Check referral code if provided
        referred_by = None
        if data.get('referral_code'):
            try:
                referred_by = User.objects.get(referral_code=data['referral_code'])
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_REFERRAL',
                        'message': 'Invalid referral code'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            user_type=data['user_type'],
            company_name_en=data['company_name_en'],
            company_name_ar=data.get('company_name_ar', ''),
            company_registration=data.get('company_registration', ''),
            vat_number=data.get('vat_number', ''),
            referred_by=referred_by,
            status='pending'
        )
        
        # Create profile
        UserProfile.objects.create(user=user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Registration successful. Your account is pending approval.',
            'data': {
                'token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 'REGISTRATION_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """Login user"""
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    user = authenticate(username=email, password=password)
    
    if not user:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if user.status == 'blocked':
        return Response({
            'success': False,
            'error': {
                'code': 'ACCOUNT_BLOCKED',
                'message': 'Your account has been blocked. Please contact support.'
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    if user.status == 'suspended':
        return Response({
            'success': False,
            'error': {
                'code': 'ACCOUNT_SUSPENDED',
                'message': 'Your account is suspended. Please contact support.'
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Update last activity
    user.last_activity = timezone.now()
    user.last_login_ip = request.META.get('REMOTE_ADDR')
    user.save(update_fields=['last_activity', 'last_login_ip'])
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'success': True,
        'data': {
            'token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserDetailSerializer(user).data
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout user"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 'LOGOUT_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """Change password"""
    serializer = ChangePasswordSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']
    
    if not user.check_password(current_password):
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_PASSWORD',
                'message': 'Current password is incorrect'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)


# ============================================================================
# User Profile Views
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    """Get user profile"""
    user = request.user
    serializer = UserDetailSerializer(user)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def profile_update_view(request):
    """Update user profile"""
    user = request.user
    serializer = UserDetailSerializer(user, data=request.data, partial=True)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# ============================================================================
# Dashboard & Statistics Views
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats_view(request):
    """Get dashboard statistics"""
    user = request.user
    
    # Get bookings count
    flight_bookings = FlightBooking.objects.filter(agent=user)
    hotel_bookings = HotelBooking.objects.filter(agent=user)
    
    # Calculate statistics
    stats = {
        'total_bookings': flight_bookings.count() + hotel_bookings.count(),
        'total_sales': float(user.profile.total_sales if hasattr(user, 'profile') else 0),
        'total_commission': float(user.profile.total_commission if hasattr(user, 'profile') else 0),
        'pending_bookings': flight_bookings.filter(status='pending').count() + hotel_bookings.filter(status='pending').count(),
        'confirmed_bookings': flight_bookings.filter(status='confirmed').count() + hotel_bookings.filter(status='confirmed').count(),
        'current_balance': float(user.current_balance),
        'wallet_balance': float(user.wallet_balance),
        'available_credit': float(user.available_credit()),
        'unread_notifications': user.notifications.filter(is_read=False).count(),
        'hajj_bookings': user.profile.hajj_bookings if hasattr(user, 'profile') else 0,
        'umrah_bookings': user.profile.umrah_bookings if hasattr(user, 'profile') else 0,
        'flight_bookings': flight_bookings.count(),
        'hotel_bookings': hotel_bookings.count(),
    }
    
    serializer = DashboardStatsSerializer(stats)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# ============================================================================
# Transaction Views
# ============================================================================

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Transaction viewset"""
    serializer_class = TransactionSerializer
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(user=user)
        
        # Filter by type
        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Date range filter
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


# Continue in next part...


# ============================================================================
# Flight Booking Views
# ============================================================================

class FlightBookingViewSet(viewsets.ModelViewSet):
    """Flight booking viewset"""
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FlightBookingListSerializer
        elif self.action == 'create':
            return FlightBookingCreateSerializer
        return FlightBookingDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = FlightBooking.objects.filter(agent=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by travel type
        travel_type = self.request.query_params.get('travel_type')
        if travel_type:
            queryset = queryset.filter(travel_type=travel_type)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(booking_id__icontains=search) |
                Q(passenger_name__icontains=search) |
                Q(pnr__icontains=search)
            )
        
        # Date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(departure_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(departure_date__lte=to_date)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set agent
        booking = serializer.save(agent=request.user)
        
        # Calculate commission
        booking.calculate_commission()
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Flight booking created successfully',
            'data': FlightBookingDetailSerializer(booking).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel flight booking"""
        booking = self.get_object()
        
        if booking.status in ['cancelled', 'refunded']:
            return Response({
                'success': False,
                'error': {
                    'code': 'ALREADY_CANCELLED',
                    'message': 'Booking is already cancelled'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'cancelled'
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Booking cancelled successfully'
        })


# ============================================================================
# Hotel Booking Views
# ============================================================================

class HotelBookingViewSet(viewsets.ModelViewSet):
    """Hotel booking viewset"""
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return HotelBookingListSerializer
        elif self.action == 'create':
            return HotelBookingCreateSerializer
        return HotelBookingDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = HotelBooking.objects.filter(agent=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(booking_id__icontains=search) |
                Q(guest_name__icontains=search) |
                Q(confirmation_number__icontains=search)
            )
        
        # Date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(check_in__gte=from_date)
        if to_date:
            queryset = queryset.filter(check_in__lte=to_date)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set agent
        booking = serializer.save(agent=request.user)
        
        return Response({
            'success': True,
            'message': 'Hotel booking created successfully',
            'data': HotelBookingDetailSerializer(booking).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel hotel booking"""
        booking = self.get_object()
        
        if booking.status in ['cancelled', 'refunded']:
            return Response({
                'success': False,
                'error': {
                    'code': 'ALREADY_CANCELLED',
                    'message': 'Booking is already cancelled'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'cancelled'
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Booking cancelled successfully'
        })


# ============================================================================
# Hajj & Umrah Package Views
# ============================================================================

class HajjPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Hajj package viewset"""
    serializer_class = HajjPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = HajjPackage.objects.filter(status='available')
        
        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(hajj_year=year)
        
        # Price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        
        return queryset.order_by('base_price')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


class UmrahPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Umrah package viewset"""
    serializer_class = UmrahPackageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        from django.utils import timezone
        today = timezone.now().date()
        
        queryset = UmrahPackage.objects.filter(
            validity_from__lte=today,
            validity_to__gte=today
        )
        
        # Filter by package type
        package_type = self.request.query_params.get('package_type')
        if package_type:
            queryset = queryset.filter(package_type=package_type)
        
        # Price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        
        # Duration
        min_duration = self.request.query_params.get('min_duration')
        max_duration = self.request.query_params.get('max_duration')
        if min_duration:
            queryset = queryset.filter(duration_days__gte=min_duration)
        if max_duration:
            queryset = queryset.filter(duration_days__lte=max_duration)
        
        return queryset.order_by('package_type', 'base_price')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


# ============================================================================
# Notification Views
# ============================================================================

class NotificationViewSet(viewsets.ModelViewSet):
    """Notification viewset"""
    serializer_class = NotificationSerializer
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({
            'success': True,
            'message': f'{count} notifications marked as read'
        })


# ============================================================================
# Document Views
# ============================================================================

class DocumentViewSet(viewsets.ModelViewSet):
    """Document viewset"""
    serializer_class = DocumentSerializer
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = Document.objects.filter(user=user)
        
        # Filter by type
        document_type = self.request.query_params.get('type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        document = serializer.save(user=request.user)
        
        return Response({
            'success': True,
            'message': 'Document uploaded successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


# ============================================================================
# Credit Request Views
# ============================================================================

class CreditRequestViewSet(viewsets.ModelViewSet):
    """Credit request viewset"""
    serializer_class = CreditRequestSerializer
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = CreditRequest.objects.filter(user=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        user = request.user
        
        # Check if user has pending request
        if CreditRequest.objects.filter(user=user, status='pending').exists():
            return Response({
                'success': False,
                'error': {
                    'code': 'PENDING_REQUEST_EXISTS',
                    'message': 'You already have a pending credit request'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        credit_request = serializer.save(
            user=user,
            current_limit=user.credit_limit
        )
        
        return Response({
            'success': True,
            'message': 'Credit request submitted successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


# ============================================================================
# Location Views
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def saudi_regions_view(request):
    """Get Saudi regions"""
    regions = SaudiRegion.objects.filter(is_active=True)
    serializer = SaudiRegionSerializer(regions, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def saudi_cities_view(request):
    """Get Saudi cities"""
    cities = SaudiCity.objects.filter(is_active=True)
    
    # Filter by region
    region_id = request.query_params.get('region')
    if region_id:
        cities = cities.filter(region_id=region_id)
    
    # Filter by type
    is_major = request.query_params.get('is_major')
    if is_major:
        cities = cities.filter(is_major_city=True)
    
    serializer = SaudiCitySerializer(cities, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# ============================================================================
# Service Supplier Views
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def service_suppliers_view(request):
    """Get service suppliers"""
    suppliers = ServiceSupplier.objects.filter(is_active=True)
    
    # Filter by type
    supplier_type = request.query_params.get('type')
    if supplier_type:
        suppliers = suppliers.filter(supplier_type=supplier_type)
    
    serializer = ServiceSupplierSerializer(suppliers, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })
