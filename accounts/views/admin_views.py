# accounts/views/admin_views.py
"""
Admin views for user management - Approve, Deny, Block users
Production Ready
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from ..models import (
    User, UserProfile, Document, UserActivityLog, 
    Notification, Transaction, FlightBooking, HotelBooking
)


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is admin"""
    
    def test_func(self):
        return self.request.user.user_type == 'admin'
    
    def handle_no_permission(self):
        messages.error(self.request, _('You do not have permission to access this page.'))
        return redirect('accounts:dashboard')


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin dashboard with full user management"""
    template_name = 'accounts/dashboard/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        pending_users = User.objects.filter(status='pending').count()
        blocked_users = User.objects.filter(status='blocked').count()
        
        # Revenue stats
        revenue_30_days = Transaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30),
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Bookings stats
        total_bookings = FlightBooking.objects.count() + HotelBooking.objects.count()
        
        # Pending approvals
        pending_approvals = User.objects.filter(
            Q(status='pending') | Q(status='under_review')
        ).count()
        
        pending_kyc = User.objects.filter(
            kyc_submitted__isnull=False,
            kyc_verified=False
        ).count()
        
        # Recent data
        pending_users_list = User.objects.filter(
            Q(status='pending') | Q(status='under_review')
        ).select_related('profile').prefetch_related('documents')[:10]
        
        recent_users = User.objects.all().order_by('-created_at')[:10]
        
        # Recent admin activities
        recent_activities = UserActivityLog.objects.filter(
            Q(activity_type__in=['user_approve', 'user_reject', 'user_block', 'user_suspend'])
        ).select_related('user', 'target_user').order_by('-created_at')[:10]
        
        # Chart data
        registration_labels = []
        registration_data = []
        
        # Last 7 days registration data
        for i in range(6, -1, -1):
            date = (timezone.now() - timedelta(days=i)).date()
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
        
        context.update({
            'page_title': _('Admin Dashboard'),
            'stats': {
                'total_users': total_users,
                'active_users_percentage': round((active_users / total_users * 100) if total_users > 0 else 0, 1),
                'pending_approvals': pending_approvals,
                'pending_kyc': pending_kyc,
                'total_revenue': abs(revenue_30_days),
                'revenue_growth': 12,  # Placeholder
                'total_bookings': total_bookings,
                'bookings_growth': 8,  # Placeholder
                'new_users_30_days': User.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=30)
                ).count(),
                'monthly_transactions': Transaction.objects.filter(
                    created_at__month=timezone.now().month
                ).count(),
                'monthly_revenue': Transaction.objects.filter(
                    created_at__month=timezone.now().month,
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
                'monthly_bookings': FlightBooking.objects.filter(
                    created_at__month=timezone.now().month
                ).count() + HotelBooking.objects.filter(
                    created_at__month=timezone.now().month
                ).count(),
                'monthly_booking_value': FlightBooking.objects.filter(
                    created_at__month=timezone.now().month
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            },
            'pending_users': pending_users_list,
            'recent_users': recent_users,
            'recent_activities': recent_activities,
            'registration_labels': json.dumps(registration_labels),
            'registration_data': json.dumps(registration_data),
            'status_distribution': json.dumps(status_distribution),
        })
        
        return context


class UserListView(AdminRequiredMixin, ListView):
    """List all users with filtering and search"""
    model = User
    template_name = 'accounts/admin/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().select_related('profile').order_by('-created_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by user type
        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(company_name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('User Management')
        context['status_choices'] = User.Status.choices
        context['user_type_choices'] = User.UserType.choices
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(status='active').count()
        context['pending_users'] = User.objects.filter(status='pending').count()
        return context


class UserDetailView(AdminRequiredMixin, DetailView):
    """User detail view for admin"""
    model = User
    template_name = 'accounts/admin/user_detail.html'
    context_object_name = 'target_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        context.update({
            'page_title': f'User Details - {user.email}',
            'documents': user.documents.all(),
            'transactions': user.transactions.all().order_by('-created_at')[:20],
            'bookings': list(FlightBooking.objects.filter(agent=user)[:10]) + 
                       list(HotelBooking.objects.filter(agent=user)[:10]),
            'activity_logs': UserActivityLog.objects.filter(user=user).order_by('-created_at')[:20],
            'notifications': Notification.objects.filter(user=user).order_by('-created_at')[:10],
        })
        
        return context


class PendingApprovalsView(AdminRequiredMixin, ListView):
    """View pending user approvals"""
    template_name = 'accounts/admin/pending_approvals.html'
    context_object_name = 'pending_users'
    paginate_by = 20
    
    def get_queryset(self):
        return User.objects.filter(
            Q(status='pending') | Q(status='under_review')
        ).select_related('profile').prefetch_related('documents').order_by('created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Pending Approvals')
        context['total_pending'] = self.get_queryset().count()
        return context


class KYCReviewView(AdminRequiredMixin, ListView):
    """Review KYC documents"""
    template_name = 'accounts/admin/kyc_review.html'
    context_object_name = 'kyc_documents'
    paginate_by = 15
    
    def get_queryset(self):
        return Document.objects.filter(
            status='pending'
        ).select_related('user').order_by('created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('KYC Review')
        context['total_pending'] = self.get_queryset().count()
        return context


# API Views for AJAX actions
class UserStatusUpdateView(AdminRequiredMixin, TemplateView):
    """Update user status via AJAX"""
    
    def post(self, request, *args, **kwargs):
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        
        try:
            user = User.objects.get(id=user_id)
            admin = request.user
            
            # Map actions to status
            status_mapping = {
                'approve': 'active',
                'reject': 'rejected',
                'block': 'blocked',
                'suspend': 'suspended',
                'active': 'active',
                'pending': 'pending',
                'under_review': 'under_review',
            }
            
            new_status = status_mapping.get(action)
            if not new_status:
                return JsonResponse({
                    'success': False,
                    'message': _('Invalid action')
                })
            
            old_status = user.status
            user.status = new_status
            
            # Additional actions based on status
            if action == 'approve':
                user.is_active = True
                user.kyc_verified = True
                # Send approval notification
                Notification.objects.create(
                    user=user,
                    notification_type='success',
                    title='Account Approved',
                    message=f'Your account has been approved by {admin.email}. You can now access all features.'
                )
            elif action in ['block', 'suspend']:
                user.is_active = False
                # Send suspension/block notification
                Notification.objects.create(
                    user=user,
                    notification_type='error',
                    title=f'Account {action.title()}ed',
                    message=f'Your account has been {action}ed. Reason: {reason}'
                )
            
            user.save()
            
            # Log activity
            UserActivityLog.objects.create(
                user=admin,
                target_user=user,
                activity_type=f'user_{action}',
                description=f'Changed user status from {old_status} to {new_status}',
                ip_address=self.get_client_ip(request),
                metadata={
                    'old_status': old_status,
                    'new_status': new_status,
                    'reason': reason,
                    'user_id': user_id
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': _(f'User status updated to {new_status}'),
                'new_status': new_status,
                'status_display': user.get_status_display()
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('User not found')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': _(f'Error: {str(e)}')
            })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentStatusUpdateView(AdminRequiredMixin, TemplateView):
    """Update document status via AJAX"""
    
    def post(self, request, *args, **kwargs):
        document_id = request.POST.get('document_id')
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        try:
            document = Document.objects.get(id=document_id)
            admin = request.user
            
            old_status = document.status
            document.status = status
            document.verification_notes = notes
            document.verified_by = admin
            document.verified_at = timezone.now()
            document.save()
            
            # Update user KYC status if all documents are verified
            user = document.user
            if status == 'verified':
                all_documents = user.documents.all()
                if all(doc.status == 'verified' for doc in all_documents):
                    user.kyc_verified = True
                    user.save()
                    
                    Notification.objects.create(
                        user=user,
                        notification_type='success',
                        title='KYC Verified',
                        message='All your documents have been verified. Your KYC is now complete.'
                    )
            
            # Log activity
            UserActivityLog.objects.create(
                user=admin,
                target_user=user,
                activity_type='document_verification',
                description=f'Document {document.get_document_type_display()} status changed from {old_status} to {status}',
                ip_address=self.get_client_ip(request),
                metadata={
                    'document_type': document.document_type,
                    'old_status': old_status,
                    'new_status': status,
                    'notes': notes
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': _(f'Document status updated to {status}'),
                'new_status': status
            })
            
        except Document.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Document not found')
            })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AdminActivityLogsView(AdminRequiredMixin, ListView):
    """View admin activity logs"""
    template_name = 'accounts/admin/activity_logs.html'
    context_object_name = 'activities'
    paginate_by = 25
    
    def get_queryset(self):
        return UserActivityLog.objects.filter(
            activity_type__in=[
                'user_approve', 'user_reject', 'user_block', 'user_suspend',
                'document_verification', 'user_create', 'user_update'
            ]
        ).select_related('user', 'target_user').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Admin Activity Logs')
        return context


class SystemSettingsView(AdminRequiredMixin, TemplateView):
    """System settings view"""
    template_name = 'accounts/admin/system_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('System Settings')
        return context