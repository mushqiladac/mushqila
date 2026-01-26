# accounts/views/business_views.py
"""
Business operation views for B2B Travel Argentina
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from datetime import datetime, timedelta

from ..models import (
    User, AgentHierarchy, CreditRequest, IPWhitelist,
    Document, UserActivityLog, Transaction
)
from ..forms import (
    AgentHierarchyForm, CreditRequestForm, IPWhitelistForm,
    KYCVerificationForm
)


class AgentHierarchyView(LoginRequiredMixin, TemplateView):
    """Agent hierarchy view"""
    
    template_name = 'accounts/business/agent_hierarchy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get hierarchy based on user type
        if user.user_type == User.UserType.ADMIN:
            # Admin can see all hierarchies
            hierarchies = AgentHierarchy.objects.filter(is_active=True)
        elif user.user_type == User.UserType.SUPER_AGENT:
            # Super agent can see their sub-agents
            hierarchies = AgentHierarchy.objects.filter(
                parent_agent=user,
                is_active=True
            )
        else:
            hierarchies = AgentHierarchy.objects.none()
        
        # Get child agents
        child_agents = user.children_agents.filter(is_active=True)
        
        # Get parent agent if any
        parent_agent = None
        try:
            parent_hierarchy = user.parent_hierarchy
            parent_agent = parent_hierarchy.parent_agent
        except:
            pass
        
        context.update({
            'page_title': _('Agent Hierarchy'),
            'hierarchies': hierarchies,
            'child_agents': child_agents,
            'parent_agent': parent_agent,
            'can_add_agent': user.user_type in [User.UserType.ADMIN, User.UserType.SUPER_AGENT],
        })
        
        return context


class AddAgentHierarchyView(LoginRequiredMixin, CreateView):
    """Add agent hierarchy view"""
    
    template_name = 'accounts/business/add_agent_hierarchy.html'
    form_class = AgentHierarchyForm
    success_url = reverse_lazy('agent_hierarchy')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                hierarchy = form.save(commit=False)
                
                # Set commission share default
                if not hierarchy.commission_share:
                    hierarchy.commission_share = 10.00  # Default 10%
                
                hierarchy.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=self.request.user,
                    activity_type=UserActivityLog.ActivityType.SYSTEM,
                    description=f"Added {hierarchy.child_agent.email} as sub-agent",
                    ip_address=self.get_client_ip(),
                    success=True,
                    metadata={
                        'parent_agent': hierarchy.parent_agent.email,
                        'child_agent': hierarchy.child_agent.email,
                        'commission_share': str(hierarchy.commission_share)
                    }
                )
                
                messages.success(self.request, _('Agent added to hierarchy successfully!'))
                return redirect(self.success_url)
        
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Add Sub-Agent')
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class CreditRequestView(LoginRequiredMixin, CreateView):
    """Credit request view"""
    
    template_name = 'accounts/business/credit_request.html'
    form_class = CreditRequestForm
    success_url = reverse_lazy('credit_request_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                credit_request = form.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=self.request.user,
                    activity_type=UserActivityLog.ActivityType.CREDIT_REQUEST,
                    description=f"Credit limit increase requested: {credit_request.current_limit} → {credit_request.requested_limit}",
                    ip_address=self.get_client_ip(),
                    success=True,
                    metadata={
                        'current_limit': str(credit_request.current_limit),
                        'requested_limit': str(credit_request.requested_limit)
                    }
                )
                
                # Send notification to admins
                self.notify_admins(credit_request)
                
                messages.success(self.request, _('Credit request submitted successfully!'))
                return redirect(self.success_url)
        
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def notify_admins(self, credit_request):
        """Send notification to admins about credit request"""
        admins = User.objects.filter(
            user_type=User.UserType.ADMIN,
            is_active=True
        )
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type=Notification.NotificationType.SYSTEM,
                title=f'New Credit Request',
                message=f'{credit_request.user.get_full_name()} has requested credit limit increase.',
                action_url=reverse_lazy('admin_credit_review')
            )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Request Credit Increase')
        context['current_limit'] = self.request.user.credit_limit
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class CreditRequestListView(LoginRequiredMixin, ListView):
    """Credit request list view"""
    
    template_name = 'accounts/business/credit_request_list.html'
    context_object_name = 'credit_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            # Admin can see all requests
            queryset = CreditRequest.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            # Super agent can see requests from their sub-agents
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            queryset = CreditRequest.objects.filter(user__in=sub_agents)
        else:
            # Regular users can only see their own requests
            queryset = CreditRequest.objects.filter(user=user)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Credit Requests')
        return context


class CreditRequestDetailView(LoginRequiredMixin, DetailView):
    """Credit request detail view"""
    
    template_name = 'accounts/business/credit_request_detail.html'
    model = CreditRequest
    context_object_name = 'credit_request'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            return CreditRequest.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            return CreditRequest.objects.filter(user__in=sub_agents)
        else:
            return CreditRequest.objects.filter(user=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Credit Request Details')
        context['can_approve'] = self.request.user.user_type in [User.UserType.ADMIN, User.UserType.SUPER_AGENT]
        return context


class ApproveCreditRequestView(LoginRequiredMixin, View):
    """Approve credit request view"""
    
    def post(self, request, pk):
        credit_request = get_object_or_404(CreditRequest, pk=pk)
        
        # Check permissions
        if not request.user.user_type in [User.UserType.ADMIN, User.UserType.SUPER_AGENT]:
            messages.error(request, _('You do not have permission to approve credit requests.'))
            return redirect('credit_request_detail', pk=pk)
        
        if credit_request.status != CreditRequest.Status.PENDING:
            messages.error(request, _('This credit request has already been processed.'))
            return redirect('credit_request_detail', pk=pk)
        
        try:
            with transaction.atomic():
                # Update user credit limit
                user = credit_request.user
                user.credit_limit = credit_request.requested_limit
                user.save()
                
                # Update credit request
                credit_request.status = CreditRequest.Status.APPROVED
                credit_request.reviewed_by = request.user
                credit_request.review_notes = request.POST.get('review_notes', '')
                credit_request.approved_at = timezone.now()
                credit_request.save()
                
                # Create transaction record
                Transaction.objects.create(
                    user=user,
                    transaction_type=Transaction.TransactionType.ADJUSTMENT,
                    amount=credit_request.get_increase_amount(),
                    currency='SAR',
                    status=Transaction.Status.COMPLETED,
                    description=f'Credit limit increased by {credit_request.get_increase_amount()} SAR',
                    balance_before=credit_request.current_limit,
                    balance_after=credit_request.requested_limit,
                    metadata={'credit_request_id': str(credit_request.id)}
                )
                
                # Log activity
                UserActivityLog.objects.create(
                    user=request.user,
                    activity_type=UserActivityLog.ActivityType.SYSTEM,
                    description=f"Approved credit request for {user.email}: {credit_request.current_limit} → {credit_request.requested_limit}",
                    ip_address=self.get_client_ip(request),
                    success=True
                )
                
                # Send notification to user
                Notification.objects.create(
                    user=user,
                    notification_type=Notification.NotificationType.SUCCESS,
                    title='Credit Limit Approved',
                    message=f'Your credit limit has been increased to {credit_request.requested_limit} SAR.',
                    action_url=reverse_lazy('credit_request_detail', kwargs={'pk': credit_request.pk})
                )
                
                messages.success(request, _('Credit request approved successfully!'))
        
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('credit_request_detail', pk=pk)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RejectCreditRequestView(LoginRequiredMixin, View):
    """Reject credit request view"""
    
    def post(self, request, pk):
        credit_request = get_object_or_404(CreditRequest, pk=pk)
        
        # Check permissions
        if not request.user.user_type in [User.UserType.ADMIN, User.UserType.SUPER_AGENT]:
            messages.error(request, _('You do not have permission to reject credit requests.'))
            return redirect('credit_request_detail', pk=pk)
        
        if credit_request.status != CreditRequest.Status.PENDING:
            messages.error(request, _('This credit request has already been processed.'))
            return redirect('credit_request_detail', pk=pk)
        
        try:
            with transaction.atomic():
                # Update credit request
                credit_request.status = CreditRequest.Status.REJECTED
                credit_request.reviewed_by = request.user
                credit_request.review_notes = request.POST.get('review_notes', '')
                credit_request.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=request.user,
                    activity_type=UserActivityLog.ActivityType.SYSTEM,
                    description=f"Rejected credit request for {credit_request.user.email}",
                    ip_address=self.get_client_ip(request),
                    success=True
                )
                
                # Send notification to user
                Notification.objects.create(
                    user=credit_request.user,
                    notification_type=Notification.NotificationType.ERROR,
                    title='Credit Request Rejected',
                    message=f'Your credit limit increase request has been rejected.',
                    action_url=reverse_lazy('credit_request_detail', kwargs={'pk': credit_request.pk})
                )
                
                messages.success(request, _('Credit request rejected.'))
        
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('credit_request_detail', pk=pk)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class IPWhitelistView(LoginRequiredMixin, ListView):
    """IP whitelist view"""
    
    template_name = 'accounts/business/ip_whitelist.html'
    context_object_name = 'whitelisted_ips'
    paginate_by = 20
    
    def get_queryset(self):
        return IPWhitelist.objects.filter(
            user=self.request.user,
            is_active=True
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('IP Whitelist')
        return context


class AddIPWhitelistView(LoginRequiredMixin, CreateView):
    """Add IP to whitelist view"""
    
    template_name = 'accounts/business/add_ip_whitelist.html'
    form_class = IPWhitelistForm
    success_url = reverse_lazy('ip_whitelist')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        ip_whitelist = form.save()
        
        # Log activity
        UserActivityLog.objects.create(
            user=self.request.user,
            activity_type=UserActivityLog.ActivityType.SYSTEM,
            description=f"Added IP to whitelist: {ip_whitelist.ip_address}",
            ip_address=self.get_client_ip(),
            success=True
        )
        
        messages.success(self.request, _('IP added to whitelist successfully!'))
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Add IP to Whitelist')
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class RemoveIPWhitelistView(LoginRequiredMixin, View):
    """Remove IP from whitelist view"""
    
    def post(self, request, pk):
        ip_whitelist = get_object_or_404(
            IPWhitelist, 
            pk=pk, 
            user=request.user
        )
        
        ip_whitelist.is_active = False
        ip_whitelist.save()
        
        # Log activity
        UserActivityLog.objects.create(
            user=request.user,
            activity_type=UserActivityLog.ActivityType.SYSTEM,
            description=f"Removed IP from whitelist: {ip_whitelist.ip_address}",
            ip_address=self.get_client_ip(request),
            success=True
        )
        
        messages.success(request, _('IP removed from whitelist.'))
        return redirect('ip_whitelist')
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class KYCReviewListView(LoginRequiredMixin, ListView):
    """KYC review list view (admin only)"""
    
    template_name = 'accounts/business/kyc_review_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        if not self.request.user.user_type == User.UserType.ADMIN:
            return Document.objects.none()
        
        return Document.objects.filter(
            status=Document.Status.PENDING
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('KYC Review')
        return context


class KYCReviewDetailView(LoginRequiredMixin, DetailView):
    """KYC review detail view (admin only)"""
    
    template_name = 'accounts/business/kyc_review_detail.html'
    model = Document
    context_object_name = 'document'
    
    def get_queryset(self):
        if not self.request.user.user_type == User.UserType.ADMIN:
            return Document.objects.none()
        
        return Document.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('KYC Document Review')
        context['form'] = KYCVerificationForm(document=self.object)
        return context


class VerifyKYCDocumentView(LoginRequiredMixin, View):
    """Verify KYC document view (admin only)"""
    
    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        
        if not request.user.user_type == User.UserType.ADMIN:
            messages.error(request, _('You do not have permission to verify documents.'))
            return redirect('kyc_review_detail', pk=pk)
        
        form = KYCVerificationForm(request.POST, document=document)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update document
                    document.status = form.cleaned_data['status']
                    document.verification_notes = form.cleaned_data['verification_notes']
                    document.verified_by = request.user
                    document.verified_at = timezone.now()
                    document.save()
                    
                    # Check if all required documents are verified
                    user = document.user
                    self.check_user_kyc_status(user)
                    
                    # Log activity
                    UserActivityLog.objects.create(
                        user=request.user,
                        activity_type=UserActivityLog.ActivityType.COMPLIANCE,
                        description=f"Verified document: {document.get_document_type_display()} for {user.email}",
                        ip_address=self.get_client_ip(request),
                        success=True,
                        metadata={
                            'document_type': document.document_type,
                            'status': document.status,
                            'user': user.email
                        }
                    )
                    
                    # Send notification to user
                    if document.status == Document.Status.VERIFIED:
                        Notification.objects.create(
                            user=user,
                            notification_type=Notification.NotificationType.SUCCESS,
                            title='Document Verified',
                            message=f'Your {document.get_document_type_display()} has been verified.',
                            action_url=reverse_lazy('kyc')
                        )
                    else:
                        Notification.objects.create(
                            user=user,
                            notification_type=Notification.NotificationType.ERROR,
                            title='Document Rejected',
                            message=f'Your {document.get_document_type_display()} has been rejected. Please review and resubmit.',
                            action_url=reverse_lazy('kyc')
                        )
                    
                    messages.success(request, _('Document verification updated successfully!'))
            
            except Exception as e:
                messages.error(request, str(e))
        
        else:
            messages.error(request, _('Please correct the errors below.'))
        
        return redirect('kyc_review_detail', pk=pk)
    
    def check_user_kyc_status(self, user):
        """Check if user's KYC is complete"""
        required_docs = self.get_required_documents(user)
        
        verified_docs = Document.objects.filter(
            user=user,
            document_type__in=required_docs,
            status=Document.Status.VERIFIED
        ).values_list('document_type', flat=True)
        
        # Check if all required documents are verified
        if set(required_docs).issubset(set(verified_docs)):
            user.kyc_verified = True
            user.save()
            
            # Send notification
            Notification.objects.create(
                user=user,
                notification_type=Notification.NotificationType.SUCCESS,
                title='KYC Verification Complete',
                message='Your KYC verification is complete. You can now use all platform features.',
                action_url=reverse_lazy('dashboard')
            )
    
    def get_required_documents(self, user):
        """Get required documents based on user type"""
        if user.user_type in [User.UserType.AGENT, User.UserType.SUB_AGENT, User.UserType.SUPER_AGENT]:
            return [
                Document.DocumentType.SAUDI_ID,
                Document.DocumentType.COMMERCIAL_REGISTRATION,
                Document.DocumentType.VAT_CERTIFICATE,
            ]
        elif user.user_type == User.UserType.CORPORATE:
            return [
                Document.DocumentType.SAUDI_ID,
                Document.DocumentType.COMMERCIAL_REGISTRATION,
                Document.DocumentType.VAT_CERTIFICATE,
            ]
        elif user.user_type == User.UserType.SUPPLIER:
            return [
                Document.DocumentType.SAUDI_ID,
                Document.DocumentType.TRADE_LICENSE,
                Document.DocumentType.VAT_CERTIFICATE,
            ]
        return []
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip