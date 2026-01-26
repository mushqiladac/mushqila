# accounts/views/user_views.py
"""
User profile and management views for B2B Travel Mushqila - Saudi Arabia
FINAL PRODUCTION READY VERSION - FIXED Sum import
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Sum  # ✅ IMPORTANT: Add this import
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import json

from ..models import (
    User, UserProfile, Document, UserActivityLog, 
    Notification, Transaction, LoginHistory
)
from ..forms import (
    UserUpdateForm, UserProfileForm, CustomPasswordChangeForm,
    DocumentUploadForm, KYCVerificationForm
)


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""
    
    template_name = 'accounts/profile/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user profile
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
        
        # Get documents
        documents = Document.objects.filter(user=user).order_by('-created_at')
        
        # Get recent activity
        recent_activity = UserActivityLog.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        # Get notifications
        notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        # Get user statistics - WITH FIXED IMPORTS
        total_bookings = 0
        total_commission = Decimal('0.00')
        
        try:
            # Import inside try block to handle missing models
            from ..models.travel import FlightBooking, HotelBooking
            from ..models.financial import CommissionTransaction
            
            # Get bookings count
            total_flight_bookings = FlightBooking.objects.filter(agent=user).count()
            total_hotel_bookings = HotelBooking.objects.filter(agent=user).count()
            total_bookings = total_flight_bookings + total_hotel_bookings
            
            # Get total commission - FIXED: Using Sum from django.db.models
            commission_result = CommissionTransaction.objects.filter(
                agent=user
            ).aggregate(total=Sum('amount'))
            total_commission = commission_result['total'] or Decimal('0.00')
            
        except ImportError:
            # If models don't exist, use default values
            pass
        except Exception as e:
            print(f"Error loading user stats: {e}")
        
        context.update({
            'page_title': _('My Profile'),
            'profile': profile,
            'documents': documents,
            'recent_activity': recent_activity,
            'notifications': notifications,
            'recent_transactions': recent_transactions,
            'kyc_completed': user.kyc_verified,
            'total_bookings': total_bookings,
            'total_commission': total_commission,
            'available_credit': user.available_credit() if hasattr(user, 'available_credit') else Decimal('0.00'),
            'wallet_balance': user.wallet_balance if hasattr(user, 'wallet_balance') else Decimal('0.00'),
        })
        
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Profile update view"""
    
    template_name = 'accounts/profile/profile_edit.html'
    form_class = UserUpdateForm
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Log activity
        UserActivityLog.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            description="Profile updated",
            ip_address=self.get_client_ip(),
            metadata={'fields_updated': list(form.changed_data)}
        )
        
        messages.success(self.request, _('Profile updated successfully!'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Update Profile')
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """User profile extension update view"""
    
    template_name = 'accounts/profile/profile_edit.html'  # Using same template
    form_class = UserProfileForm
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user.profile
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Log activity
        UserActivityLog.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            description="Extended profile details updated",
            ip_address=self.get_client_ip()
        )
        
        messages.success(self.request, _('Profile details updated successfully!'))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Update Profile Details')
        context['is_extended_profile'] = True
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class PasswordChangeView(LoginRequiredMixin, View):
    """Password change view"""
    
    template_name = 'accounts/profile/security.html'
    
    def get(self, request):
        form = CustomPasswordChangeForm(request.user)
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Change Password'),
            'active_tab': 'password'
        })
    
    def post(self, request):
        form = CustomPasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                activity_type='password_change',
                description="Password changed successfully",
                ip_address=self.get_client_ip(request)
            )
            
            messages.success(request, _('Password changed successfully!'))
            return redirect('accounts:profile')
        
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Change Password'),
            'active_tab': 'password'
        })
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class KYCView(LoginRequiredMixin, TemplateView):
    """KYC verification view"""
    
    template_name = 'accounts/profile/kyc.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get documents by type
        documents = Document.objects.filter(user=user)
        required_docs = []
        optional_docs = []
        
        # Define required documents based on user type
        if user.user_type in ['agent', 'sub_agent', 'super_agent']:
            required_docs = [
                'saudi_id',
                'commercial_registration',
                'vat_certificate',
            ]
            if user.user_type != 'sub_agent':
                required_docs.append('scta_license')
        
        elif user.user_type == 'corporate':
            required_docs = [
                'saudi_id',
                'commercial_registration',
                'vat_certificate',
            ]
        
        elif user.user_type == 'supplier':
            required_docs = [
                'saudi_id',
                'trade_license',
                'vat_certificate',
            ]
        
        # Check which documents are uploaded and verified
        uploaded_docs = {}
        for doc in documents:
            uploaded_docs[doc.document_type] = {
                'document': doc,
                'status': doc.status,
                'is_valid': doc.status == 'verified'
            }
        
        # Calculate KYC progress
        total_required = len(required_docs)
        completed_required = 0
        
        for doc_type in required_docs:
            if doc_type in uploaded_docs and uploaded_docs[doc_type]['is_valid']:
                completed_required += 1
        
        progress = int((completed_required / total_required) * 100) if total_required > 0 else 0
        
        # Check if KYC can be submitted
        can_submit = completed_required == total_required
        
        # Get document type choices
        document_choices = [
            ('saudi_id', _('Saudi ID/Passport')),
            ('commercial_registration', _('Commercial Registration')),
            ('vat_certificate', _('VAT Certificate')),
            ('scta_license', _('SCTA License')),
            ('hajj_license', _('Hajj License')),
            ('trade_license', _('Trade License')),
            ('bank_statement', _('Bank Statement')),
            ('utility_bill', _('Utility Bill')),
        ]
        
        context.update({
            'page_title': _('KYC Verification'),
            'documents': documents,
            'required_docs': required_docs,
            'optional_docs': optional_docs,
            'uploaded_docs': uploaded_docs,
            'progress': progress,
            'can_submit': can_submit,
            'kyc_verified': user.kyc_verified,
            'kyc_submitted': user.kyc_submitted is not None,
            'document_choices': document_choices,
        })
        
        return context


class DocumentUploadView(LoginRequiredMixin, View):
    """Document upload view"""
    
    template_name = 'accounts/profile/kyc.html'  # Using KYC template
    
    def get(self, request, document_type=None):
        form = DocumentUploadForm()
        
        if document_type:
            form.fields['document_type'].initial = document_type
        
        # Get context from KYCView
        kyc_view = KYCView()
        kyc_view.request = request
        context = kyc_view.get_context_data()
        
        context.update({
            'form': form,
            'page_title': _('Upload Document'),
            'document_type': document_type,
            'show_upload_form': True,
        })
        
        return render(request, self.template_name, context)
    
    def post(self, request, document_type=None):
        form = DocumentUploadForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            document = form.save()
            
            # Log activity
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='document_upload',
                description=f"Document uploaded: {document.get_document_type_display()}",
                ip_address=self.get_client_ip(request),
                metadata={'document_type': document.document_type}
            )
            
            messages.success(request, _('Document uploaded successfully!'))
            return redirect('accounts:kyc')
        
        # If form invalid, show KYC page with errors
        kyc_view = KYCView()
        kyc_view.request = request
        context = kyc_view.get_context_data()
        
        context.update({
            'form': form,
            'page_title': _('Upload Document'),
            'document_type': document_type,
            'show_upload_form': True,
        })
        
        return render(request, self.template_name, context)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentDeleteView(LoginRequiredMixin, View):
    """Document delete view"""
    
    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, user=request.user)
        
        # Only allow deletion if not verified
        if document.status != 'verified':
            document_type = document.get_document_type_display()
            document.delete()
            
            # Log activity
            UserActivityLog.objects.create(
                user=request.user,
                activity_type='document_delete',
                description=f"Document deleted: {document_type}",
                ip_address=self.get_client_ip(request)
            )
            
            messages.success(request, _('Document deleted successfully!'))
        else:
            messages.error(request, _('Cannot delete verified documents.'))
        
        return redirect('accounts:kyc')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SubmitKYCView(LoginRequiredMixin, View):
    """Submit KYC for verification"""
    
    def post(self, request):
        user = request.user
        
        # Check if KYC can be submitted
        if not user.kyc_verified and not user.kyc_submitted:
            user.kyc_submitted = timezone.now()
            user.save()
            
            # Log activity
            UserActivityLog.objects.create(
                user=user,
                activity_type='kyc_submission',
                description="KYC submitted for verification",
                ip_address=self.get_client_ip(request)
            )
            
            # Send notification to admin
            self.notify_admins(user)
            
            messages.success(request, _('KYC submitted for verification!'))
        else:
            messages.error(request, _('KYC already submitted or verified.'))
        
        return redirect('accounts:kyc')
    
    def notify_admins(self, user):
        """Send notification to admins about KYC submission"""
        admins = User.objects.filter(
            user_type='admin',
            is_active=True
        )
        
        from django.urls import reverse
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type='kyc',
                title='New KYC Submission',
                message=f'{user.get_full_name()} ({user.email}) has submitted KYC for verification.',
                action_url=reverse('accounts:admin_kyc_review')
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecuritySettingsView(LoginRequiredMixin, TemplateView):
    """Security settings view"""
    
    template_name = 'accounts/profile/security.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get login history
        login_history = LoginHistory.objects.filter(
            user=user
        ).order_by('-created_at')[:20]
        
        # Get activity logs
        activity_logs = UserActivityLog.objects.filter(
            user=user
        ).order_by('-created_at')[:20]
        
        # Get IP whitelist
        from ..models.business import IPWhitelist
        ip_whitelist = IPWhitelist.objects.filter(user=user, is_active=True)
        
        context.update({
            'page_title': _('Security Settings'),
            'login_history': login_history,
            'activity_logs': activity_logs,
            'ip_whitelist': ip_whitelist,
            'two_factor_enabled': hasattr(user, 'two_factor_auth') and user.two_factor_auth,
        })
        
        return context


class NotificationListView(LoginRequiredMixin, ListView):
    """Notification list view"""
    
    template_name = 'accounts/profile/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Notifications')
        return context


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark notification as read"""
    
    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            user=request.user
        )
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        
        return JsonResponse({'success': True})


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Mark all notifications as read"""
    
    def post(self, request):
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        
        updated_count = notifications.update(
            is_read=True, 
            read_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count
        })


class ActivityLogView(LoginRequiredMixin, ListView):
    """Activity log view"""
    
    template_name = 'accounts/profile/activity_log.html'
    context_object_name = 'activity_logs'
    paginate_by = 50
    
    def get_queryset(self):
        return UserActivityLog.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Activity Log')
        return context


class ReferralView(LoginRequiredMixin, TemplateView):
    """Referral view"""
    
    template_name = 'accounts/profile/referral.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get referrals
        referrals = User.objects.filter(referred_by=user)
        
        # Calculate commission from referrals
        total_commission = Transaction.objects.filter(
            user__referred_by=user,
            transaction_type='commission'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get referral stats
        referral_stats = {
            'total_referrals': referrals.count(),
            'active_referrals': referrals.filter(status='active').count(),
            'pending_referrals': referrals.filter(status='pending').count(),
            'total_commission': total_commission,
        }
        
        # Generate referral link
        if user.referral_code:
            referral_link = self.request.build_absolute_uri(
                f'/accounts/register/?ref={user.referral_code}'
            )
        else:
            referral_link = None
        
        context.update({
            'page_title': _('Referral Program'),
            'referrals': referrals,
            'referral_stats': referral_stats,
            'referral_code': user.referral_code,
            'referral_link': referral_link,
        })
        
        return context


# URL Names for reverse lookups
PROFILE_URLS = {
    'profile': 'accounts:profile',
    'profile_edit': 'accounts:profile_edit',
    'profile_ext_edit': 'accounts:profile_ext_edit',
    'password_change': 'accounts:password_change',
    'kyc': 'accounts:kyc',
    'document_upload': 'accounts:document_upload',
    'document_delete': 'accounts:document_delete',
    'submit_kyc': 'accounts:submit_kyc',
    'security': 'accounts:security',
    'notifications': 'accounts:notifications',
    'mark_notification_read': 'accounts:mark_notification_read',
    'mark_all_notifications_read': 'accounts:mark_all_notifications_read',
    'activity_log': 'accounts:activity_log',
    'referral': 'accounts:referral',
}