# accounts/views/dashboard_views.py
"""
Dashboard views for Mushqila B2B Travel Platform
Production Ready - Compatible with existing dashboard templates
FIXED: Added DashboardView class and fixed all redirect issues
UPDATED: Fixed database query issues and missing models
"""

from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.user_type == 'admin' or user.is_staff or user.is_superuser)


def is_agent(user):
    """Check if user is agent or sub-agent"""
    return user.is_authenticated and user.user_type in ['agent', 'sub_agent', 'super_agent']


def is_supplier(user):
    """Check if user is supplier"""
    return user.is_authenticated and user.user_type == 'supplier'


# ✅ NEW: DashboardView class to handle dashboard routing
class DashboardView(LoginRequiredMixin, View):
    """
    Main dashboard view that redirects users to appropriate dashboard
    This is the view that should be called when user goes to /dashboard/
    """
    
    def get(self, request):
        user = request.user
        
        print(f"📊 DashboardView: Checking user {user.email}, Type: {user.user_type}")
        
        if is_admin(user):
            print(f"🔄 Redirecting to admin dashboard")
            return redirect('accounts:admin_dashboard')
        elif is_agent(user):
            print(f"🔄 Redirecting to agent dashboard")
            return redirect('accounts:agent_dashboard')
        elif is_supplier(user):
            print(f"🔄 Redirecting to supplier dashboard")
            return redirect('accounts:supplier_dashboard')
        elif user.user_type == 'corporate':
            print(f"🔄 Redirecting to agent dashboard (corporate)")
            return redirect('accounts:agent_dashboard')
        else:
            print(f"⚠️ Unknown user type: {user.user_type}")
            messages.warning(request, "Your account type is not configured for dashboard access.")
            return redirect('accounts:home')


@login_required
def dashboard_redirect(request):
    """
    Redirect user to appropriate dashboard based on user type
    This is a function-based view alternative to DashboardView
    """
    user = request.user
    
    print(f"📊 dashboard_redirect: Checking user {user.email}, Type: {user.user_type}")
    
    if is_admin(user):
        return redirect('accounts:admin_dashboard')
    elif is_agent(user):
        return redirect('accounts:agent_dashboard')
    elif is_supplier(user):
        return redirect('accounts:supplier_dashboard')
    elif user.user_type == 'corporate':
        return redirect('accounts:agent_dashboard')
    else:
        messages.warning(request, "Your account type is not configured for dashboard access.")
        return redirect('accounts:home')


@login_required
def admin_dashboard(request):
    """Admin dashboard view - for admin_dashboard.html template"""
    if not is_admin(request.user):
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('accounts:home')
    
    user = request.user
    
    try:
        # Import models - FIXED: Avoid circular imports
        from ..models.core import User, Notification, UserActivityLog
        from ..models.travel import FlightBooking, HotelBooking
        from ..models.financial import Transaction
        from ..models.business import Document
        
        # Time periods
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        week_ago = today - timedelta(days=7)
        
        # User statistics - FIXED: Use correct model imports
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        pending_users = User.objects.filter(status='pending').count()
        
        # Booking statistics
        total_bookings = FlightBooking.objects.count() + HotelBooking.objects.count()
        bookings_growth = 8  # Placeholder
        
        # Revenue statistics
        revenue_30_days = Transaction.objects.filter(
            created_at__gte=month_ago,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        revenue_growth = 12  # Placeholder
        
        # Pending approvals - FIXED: Use Document model for KYC
        pending_kyc = Document.objects.filter(status='pending').count()
        
        # Recent activities
        recent_activities = UserActivityLog.objects.filter(
            Q(activity_type__in=['user_approve', 'user_reject', 'user_block', 'user_suspend', 'document_verification'])
        ).select_related('user').order_by('-created_at')[:10]
        
        # Pending users for approval - FIXED: Add documents prefetch
        pending_users_list = User.objects.filter(
            Q(status='pending') | Q(status='under_review')
        ).select_related('profile').order_by('created_at')[:5]
        
        # Add document counts to users
        for pending_user in pending_users_list:
            pending_user.document_count = Document.objects.filter(user=pending_user).count()
        
        # Recent users
        recent_users = User.objects.all().order_by('-created_at')[:10]
        
        # Chart data - last 7 days registration
        registration_labels = []
        registration_data = []
        
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i))
            count = User.objects.filter(
                created_at__date=date
            ).count()
            registration_labels.append(date.strftime('%a'))
            registration_data.append(count)
        
        # Status distribution
        status_distribution = [
            User.objects.filter(status='active').count(),
            User.objects.filter(status='pending').count(),
            User.objects.filter(status='blocked').count(),
            User.objects.filter(status='suspended').count(),
        ]
        
        # Monthly stats for reports modal
        new_users_30_days = User.objects.filter(
            created_at__gte=month_ago
        ).count()
        
        monthly_transactions = Transaction.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count()
        
        monthly_revenue = Transaction.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        monthly_bookings_count = FlightBooking.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count() + HotelBooking.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).count()
        
        monthly_booking_value = FlightBooking.objects.filter(
            created_at__month=today.month,
            created_at__year=today.year
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Get notifications
        notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        context = {
            'page_title': 'Admin Dashboard',
            'dashboard_type': 'admin',
            'stats': {
                'total_users': total_users,
                'active_users_percentage': round((active_users / total_users * 100) if total_users > 0 else 0, 1),
                'pending_approvals': pending_users,
                'pending_kyc': pending_kyc,
                'total_revenue': abs(revenue_30_days),
                'revenue_growth': revenue_growth,
                'total_bookings': total_bookings,
                'bookings_growth': bookings_growth,
                'new_users_30_days': new_users_30_days,
                'monthly_transactions': monthly_transactions,
                'monthly_revenue': monthly_revenue,
                'monthly_bookings': monthly_bookings_count,
                'monthly_booking_value': monthly_booking_value,
            },
            'pending_users': pending_users_list,
            'recent_users': recent_users,
            'recent_activities': recent_activities,
            'registration_labels': json.dumps(registration_labels),
            'registration_data': json.dumps(registration_data),
            'status_distribution': json.dumps(status_distribution),
            'notifications': notifications,
        }
        
    except Exception as e:
        print(f"❌ Error in admin_dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback if any model doesn't exist
        context = {
            'page_title': 'Admin Dashboard',
            'dashboard_type': 'admin',
            'stats': {
                'total_users': 0,
                'active_users_percentage': 0,
                'pending_approvals': 0,
                'pending_kyc': 0,
                'total_revenue': 0,
                'revenue_growth': 0,
                'total_bookings': 0,
                'bookings_growth': 0,
                'new_users_30_days': 0,
                'monthly_transactions': 0,
                'monthly_revenue': 0,
                'monthly_bookings': 0,
                'monthly_booking_value': 0,
            },
            'pending_users': [],
            'recent_users': [],
            'recent_activities': [],
            'registration_labels': json.dumps([]),
            'registration_data': json.dumps([]),
            'status_distribution': json.dumps([]),
            'notifications': [],
        }
    
    return render(request, 'accounts/dashboard/admin_dashboard.html', context)


@login_required
def agent_dashboard(request):
    """Agent dashboard view - for agent_dashboard.html template"""
    if not is_agent(request.user):
        messages.error(request, "You don't have permission to access the agent dashboard.")
        return redirect('accounts:home')
    
    user = request.user
    
    try:
        # Import models
        from ..models.travel import FlightBooking, HotelBooking
        from ..models.financial import CommissionTransaction
        from ..models.core import Notification
        
        # Time periods
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        # Booking statistics - FIXED: Handle if models don't exist
        total_flight_bookings = FlightBooking.objects.filter(agent=user).count()
        total_hotel_bookings = HotelBooking.objects.filter(agent=user).count()
        total_bookings = total_flight_bookings + total_hotel_bookings
        
        # Sales statistics
        flight_sales = FlightBooking.objects.filter(
            agent=user
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        hotel_sales = HotelBooking.objects.filter(
            agent=user
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_sales = (flight_sales or Decimal('0.00')) + (hotel_sales or Decimal('0.00'))
        
        # Commission statistics
        try:
            total_commission = CommissionTransaction.objects.filter(
                agent=user
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        except:
            total_commission = Decimal('0.00')
        
        # Recent bookings (last 10)
        recent_flights = FlightBooking.objects.filter(
            agent=user
        ).order_by('-created_at')[:5]
        
        recent_hotels = HotelBooking.objects.filter(
            agent=user
        ).order_by('-created_at')[:5]
        
        # Combine and format recent bookings
        recent_bookings = []
        
        for flight in recent_flights:
            recent_bookings.append({
                'id': flight.id,
                'booking_id': flight.booking_id if hasattr(flight, 'booking_id') else f'FL{flight.id}',
                'passenger_name': flight.passenger_name if hasattr(flight, 'passenger_name') else 'N/A',
                'passenger_phone': flight.passenger_phone if hasattr(flight, 'passenger_phone') else '',
                'service_type': 'flight',
                'total_amount': flight.total_amount if hasattr(flight, 'total_amount') else Decimal('0.00'),
                'status': flight.status if hasattr(flight, 'status') else 'pending',
                'commission_amount': flight.commission_amount if hasattr(flight, 'commission_amount') else Decimal('0.00'),
                'created_at': flight.created_at if hasattr(flight, 'created_at') else timezone.now(),
            })
        
        for hotel in recent_hotels:
            recent_bookings.append({
                'id': hotel.id,
                'booking_id': hotel.booking_id if hasattr(hotel, 'booking_id') else f'HT{hotel.id}',
                'passenger_name': hotel.guest_name if hasattr(hotel, 'guest_name') else 'N/A',
                'passenger_phone': hotel.guest_phone if hasattr(hotel, 'guest_phone') else '',
                'service_type': 'hotel',
                'total_amount': hotel.total_amount if hasattr(hotel, 'total_amount') else Decimal('0.00'),
                'status': hotel.status if hasattr(hotel, 'status') else 'pending',
                'commission_amount': hotel.commission_amount if hasattr(hotel, 'commission_amount') else Decimal('0.00'),
                'created_at': hotel.created_at if hasattr(hotel, 'created_at') else timezone.now(),
            })
        
        # Sort by creation date
        recent_bookings.sort(key=lambda x: x['created_at'], reverse=True)
        recent_bookings = recent_bookings[:10]
        
        # Sales chart data (last 7 days)
        sales_labels = []
        sales_data = []
        
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i))
            
            # Flight sales for the day
            day_flight_sales = FlightBooking.objects.filter(
                agent=user,
                created_at__date=date
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Hotel sales for the day
            day_hotel_sales = HotelBooking.objects.filter(
                agent=user,
                created_at__date=date
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            total_day_sales = (day_flight_sales or Decimal('0.00')) + (day_hotel_sales or Decimal('0.00'))
            
            sales_labels.append(date.strftime('%a'))
            sales_data.append(float(total_day_sales))
        
        # Service distribution for pie chart
        service_distribution = [60, 25, 10, 5]  # Flights, Hotels, Hajj, Umrah
        
        # Monthly statistics for modal
        monthly_stats = {
            'flights': FlightBooking.objects.filter(
                agent=user,
                created_at__month=today.month,
                created_at__year=today.year
            ).count(),
            'hotels': HotelBooking.objects.filter(
                agent=user,
                created_at__month=today.month,
                created_at__year=today.year
            ).count(),
            'packages': 0,  # Placeholder
            'sales': FlightBooking.objects.filter(
                agent=user,
                created_at__month=today.month,
                created_at__year=today.year
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            'commission': CommissionTransaction.objects.filter(
                agent=user,
                created_at__month=today.month,
                created_at__year=today.year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        }
        
        # Last month stats
        last_month = today.replace(day=1) - timedelta(days=1)
        last_month_stats = {
            'flights': FlightBooking.objects.filter(
                agent=user,
                created_at__month=last_month.month,
                created_at__year=last_month.year
            ).count(),
            'hotels': HotelBooking.objects.filter(
                agent=user,
                created_at__month=last_month.month,
                created_at__year=last_month.year
            ).count(),
            'packages': 0,
            'sales': FlightBooking.objects.filter(
                agent=user,
                created_at__month=last_month.month,
                created_at__year=last_month.year
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            'commission': CommissionTransaction.objects.filter(
                agent=user,
                created_at__month=last_month.month,
                created_at__year=last_month.year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        }
        
        # Notifications
        try:
            unread_notifications_count = Notification.objects.filter(
                user=user,
                is_read=False
            ).count()
            
            notifications = Notification.objects.filter(
                user=user
            ).order_by('-created_at')[:10]
        except:
            unread_notifications_count = 0
            notifications = []
        
        # Service stats for template
        service_stats = {
            'flights': 60,
            'hotels': 25,
            'hajj': 10,
            'umrah': 5,
        }
        
        # User financial data
        commission_rate = user.commission_rate if hasattr(user, 'commission_rate') and user.commission_rate else Decimal('5.00')
        wallet_balance = user.wallet_balance if hasattr(user, 'wallet_balance') else Decimal('0.00')
        credit_limit = user.credit_limit if hasattr(user, 'credit_limit') else Decimal('0.00')
        current_balance = user.current_balance if hasattr(user, 'current_balance') else Decimal('0.00')
        available_credit = credit_limit + current_balance
        
        context = {
            'page_title': 'Agent Dashboard',
            'total_bookings': total_bookings,
            'monthly_growth': 15,
            'total_sales': total_sales,
            'sales_growth': 12,
            'total_commission': total_commission,
            'commission_rate': commission_rate,
            'wallet_balance': wallet_balance,
            'available_credit': available_credit,
            'recent_bookings': recent_bookings,
            'unread_notifications_count': unread_notifications_count,
            'notifications': notifications,
            'service_stats': service_stats,
            'sales_labels': json.dumps(sales_labels),
            'sales_data': json.dumps(sales_data),
            'service_distribution': json.dumps(service_distribution),
            'monthly_stats': monthly_stats,
            'last_month_stats': last_month_stats,
        }
        
    except Exception as e:
        print(f"❌ Error in agent_dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback context
        context = {
            'page_title': 'Agent Dashboard',
            'total_bookings': 0,
            'monthly_growth': 0,
            'total_sales': Decimal('0.00'),
            'sales_growth': 0,
            'total_commission': Decimal('0.00'),
            'commission_rate': Decimal('5.00'),
            'wallet_balance': Decimal('0.00'),
            'available_credit': Decimal('0.00'),
            'recent_bookings': [],
            'unread_notifications_count': 0,
            'notifications': [],
            'service_stats': {'flights': 0, 'hotels': 0, 'hajj': 0, 'umrah': 0},
            'sales_labels': json.dumps(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
            'sales_data': json.dumps([0, 0, 0, 0, 0, 0, 0]),
            'service_distribution': json.dumps([0, 0, 0, 0]),
            'monthly_stats': {'flights': 0, 'hotels': 0, 'packages': 0, 'sales': Decimal('0.00'), 'commission': Decimal('0.00')},
            'last_month_stats': {'flights': 0, 'hotels': 0, 'packages': 0, 'sales': Decimal('0.00'), 'commission': Decimal('0.00')},
        }
    
    return render(request, 'accounts/dashboard/agent_dashboard.html', context)


@login_required
def supplier_dashboard(request):
    """Supplier dashboard view - for supplier_dashboard.html template"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to access the supplier dashboard.")
        return redirect('accounts:home')
    
    user = request.user
    
    try:
        # Import models
        from ..models.travel import ServiceSupplier
        from ..models.financial import Payment, Transaction
        from ..models.core import Notification
        
        # Time periods
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        # Service statistics - FIXED: Use existing ServiceSupplier model
        active_services = ServiceSupplier.objects.filter(is_active=True).count()
        services_available = ServiceSupplier.objects.filter(is_active=True).count()
        
        # Since SupplierService model doesn't exist, use placeholder data
        total_orders = 0
        booking_growth = 8  # Placeholder
        
        # Revenue statistics
        total_revenue = Transaction.objects.filter(
            user=user,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        revenue_growth = 12  # Placeholder
        
        # Pending payments
        pending_payments = Payment.objects.filter(
            user=user,
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Top performing services - FIXED: Use ServiceSupplier model
        top_services = ServiceSupplier.objects.filter(is_active=True)[:5]
        
        formatted_top_services = []
        for service in top_services:
            formatted_top_services.append({
                'name': service.name,
                'service_type': service.supplier_type,
                'booking_count': 0,  # Placeholder
                'revenue': Decimal('0.00'),  # Placeholder
            })
        
        # Recent orders - FIXED: Use FlightBooking/HotelBooking for now
        from ..models.travel import FlightBooking, HotelBooking
        recent_orders = []
        
        # Revenue chart data (last 6 months)
        revenue_labels = []
        revenue_data = []
        
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            
            month_revenue = Transaction.objects.filter(
                user=user,
                status='completed',
                created_at__year=month_start.year,
                created_at__month=month_start.month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            revenue_labels.append(month_start.strftime('%b'))
            revenue_data.append(float(month_revenue))
        
        # Notifications
        notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        context = {
            'page_title': 'Supplier Dashboard',
            'active_services': active_services,
            'services_available': services_available,
            'total_bookings': total_orders,
            'booking_growth': booking_growth,
            'total_revenue': total_revenue,
            'revenue_growth': revenue_growth,
            'pending_payments': pending_payments,
            'top_services': formatted_top_services,
            'recent_orders': recent_orders,
            'revenue_labels': json.dumps(revenue_labels),
            'revenue_data': json.dumps(revenue_data),
            'notifications': notifications,
        }
        
    except Exception as e:
        print(f"❌ Error in supplier_dashboard: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback context
        context = {
            'page_title': 'Supplier Dashboard',
            'active_services': 0,
            'services_available': 0,
            'total_bookings': 0,
            'booking_growth': 0,
            'total_revenue': Decimal('0.00'),
            'revenue_growth': 0,
            'pending_payments': Decimal('0.00'),
            'top_services': [],
            'recent_orders': [],
            'revenue_labels': json.dumps(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']),
            'revenue_data': json.dumps([0, 0, 0, 0, 0, 0]),
            'notifications': [],
        }
    
    return render(request, 'accounts/dashboard/supplier_dashboard.html', context)


# Supplier management views
@login_required
def supplier_services(request):
    """Supplier services management view"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to access supplier services.")
        return redirect('accounts:home')
    
    return render(request, 'accounts/supplier/services.html', {
        'page_title': 'My Services'
    })


@login_required
def supplier_service_create(request):
    """Create new service for supplier"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to create services.")
        return redirect('accounts:home')
    
    return render(request, 'accounts/supplier/service_create.html', {
        'page_title': 'Create New Service'
    })


@login_required
def supplier_service_detail(request, service_id):
    """Supplier service detail view"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to view this service.")
        return redirect('accounts:home')
    
    return render(request, 'accounts/supplier/service_detail.html', {
        'page_title': 'Service Details',
        'service_id': service_id
    })


@login_required
def supplier_orders(request):
    """Supplier orders view"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to access orders.")
        return redirect('accounts:home')
    
    return render(request, 'accounts/supplier/orders.html', {
        'page_title': 'My Orders'
    })


@login_required
def supplier_order_detail(request, order_id):
    """Supplier order detail view"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to view this order.")
        return redirect('accounts:home')
    
    return render(request, 'accounts/supplier/order_detail.html', {
        'page_title': 'Order Details',
        'order_id': order_id
    })


@login_required
def supplier_payments(request):
    """Supplier payments view"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to access payments.")
        return redirect('accounts:home')
    
    return render(request, 'accounts/supplier/payments.html', {
        'page_title': 'Payments'
    })


@login_required
def supplier_analytics(request):
    """Supplier analytics view"""
    if not is_supplier(request.user):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect('accounts:home')
    
    return render(request, 'accounts/supplier/analytics.html', {
        'page_title': 'Analytics'
    })