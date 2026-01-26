# accounts/views/financial_views.py
"""
Financial views for B2B Travel Argentina
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..models import (
    User, Transaction, Payment, Invoice, Refund,
    CommissionTransaction, UserActivityLog
)
from ..forms import (
    PaymentForm, DepositForm, WithdrawalForm,
    RefundRequestForm, CreditLimitForm
)


class WalletView(LoginRequiredMixin, TemplateView):
    """Wallet view"""
    
    template_name = 'accounts/financial/wallet.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get wallet statistics
        wallet_stats = {
            'balance': user.wallet_balance,
            'credit_limit': user.credit_limit,
            'available_credit': user.available_credit(),
            'current_balance': user.current_balance,
            'total_deposits': Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                status=Transaction.Status.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
            'total_withdrawals': Transaction.objects.filter(
                user=user,
                transaction_type=Transaction.TransactionType.WITHDRAWAL,
                status=Transaction.Status.COMPLETED
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'),
        }
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        # Get pending payments
        pending_payments = Payment.objects.filter(
            user=user,
            status=Payment.PaymentStatus.PENDING
        ).order_by('-created_at')[:5]
        
        context.update({
            'page_title': _('My Wallet'),
            'wallet_stats': wallet_stats,
            'recent_transactions': recent_transactions,
            'pending_payments': pending_payments,
            'user': user,
        })
        
        return context


class DepositView(LoginRequiredMixin, View):
    """Deposit view"""
    
    template_name = 'accounts/financial/deposit.html'
    
    def get(self, request):
        form = DepositForm(user=request.user)
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Deposit Funds'),
            'user': request.user,
        })
    
    def post(self, request):
        form = DepositForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    deposit_amount = form.cleaned_data['deposit_amount']
                    deposit_method = form.cleaned_data['deposit_method']
                    reference_number = form.cleaned_data['reference_number']
                    
                    # Create payment record
                    payment = Payment.objects.create(
                        user=request.user,
                        amount=deposit_amount,
                        vat_amount=deposit_amount * Decimal('0.15'),
                        payment_method=deposit_method,
                        status=Payment.PaymentStatus.PENDING,
                        reference_number=reference_number,
                        description=f'Deposit via {deposit_method}',
                    )
                    
                    # Create pending transaction
                    Transaction.objects.create(
                        user=request.user,
                        transaction_type=Transaction.TransactionType.DEPOSIT,
                        amount=deposit_amount,
                        currency='SAR',
                        status=Transaction.Status.PENDING,
                        description=f'Deposit via {deposit_method} - Reference: {reference_number}',
                        balance_before=request.user.wallet_balance,
                        balance_after=request.user.wallet_balance,
                        metadata={
                            'payment_id': payment.payment_id,
                            'deposit_method': deposit_method,
                            'reference_number': reference_number
                        }
                    )
                    
                    # Log activity
                    UserActivityLog.objects.create(
                        user=request.user,
                        activity_type=UserActivityLog.ActivityType.DEPOSIT,
                        description=f"Deposit requested: {deposit_amount} SAR via {deposit_method}",
                        ip_address=self.get_client_ip(request),
                        success=True,
                        metadata={'amount': str(deposit_amount)}
                    )
                    
                    # If bank transfer, notify admin for approval
                    if deposit_method == 'bank_transfer':
                        self.notify_admins_of_deposit(payment)
                        messages.success(
                            request,
                            _('Deposit request submitted! Please wait for admin approval.')
                        )
                    else:
                        # For instant payment methods, mark as completed
                        payment.status = Payment.PaymentStatus.SUCCESS
                        payment.completed_at = timezone.now()
                        payment.save()
                        
                        # Update transaction
                        transaction = Transaction.objects.filter(
                            metadata__payment_id=payment.payment_id
                        ).first()
                        if transaction:
                            transaction.status = Transaction.Status.COMPLETED
                            transaction.balance_after = request.user.wallet_balance + deposit_amount
                            transaction.save()
                        
                        # Update user wallet
                        request.user.wallet_balance = F('wallet_balance') + deposit_amount
                        request.user.save()
                        
                        messages.success(
                            request,
                            _('Deposit successful! %(amount)s SAR has been added to your wallet.') % 
                            {'amount': deposit_amount}
                        )
                    
                    return redirect('wallet')
            
            except Exception as e:
                messages.error(request, str(e))
        
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Deposit Funds'),
            'user': request.user,
        })
    
    def notify_admins_of_deposit(self, payment):
        """Notify admins about bank transfer deposit"""
        admins = User.objects.filter(
            user_type=User.UserType.ADMIN,
            is_active=True
        )
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type=Notification.NotificationType.PAYMENT,
                title='New Deposit Request',
                message=f'{payment.user.get_full_name()} has requested a deposit of {payment.amount} SAR via bank transfer.',
                action_url=reverse_lazy('admin_payment_review')
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class WithdrawalView(LoginRequiredMixin, View):
    """Withdrawal view"""
    
    template_name = 'accounts/financial/withdrawal.html'
    
    def get(self, request):
        form = WithdrawalForm(user=request.user)
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Withdraw Funds'),
            'user': request.user,
        })
    
    def post(self, request):
        form = WithdrawalForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    withdrawal_amount = form.cleaned_data['withdrawal_amount']
                    withdrawal_method = form.cleaned_data['withdrawal_method']
                    bank_account = form.cleaned_data['bank_account']
                    
                    # Check if user has sufficient balance
                    if withdrawal_amount > request.user.wallet_balance:
                        messages.error(
                            request,
                            _('Insufficient wallet balance.')
                        )
                        return redirect('withdrawal')
                    
                    # Create transaction
                    transaction = Transaction.objects.create(
                        user=request.user,
                        transaction_type=Transaction.TransactionType.WITHDRAWAL,
                        amount=-withdrawal_amount,
                        currency='SAR',
                        status=Transaction.Status.PENDING,
                        description=f'Withdrawal via {withdrawal_method}',
                        balance_before=request.user.wallet_balance,
                        balance_after=request.user.wallet_balance - withdrawal_amount,
                        metadata={
                            'withdrawal_method': withdrawal_method,
                            'bank_account': bank_account
                        }
                    )
                    
                    # Update user wallet (temporarily hold the amount)
                    request.user.wallet_balance = F('wallet_balance') - withdrawal_amount
                    request.user.save()
                    
                    # Log activity
                    UserActivityLog.objects.create(
                        user=request.user,
                        activity_type=UserActivityLog.ActivityType.WITHDRAWAL,
                        description=f"Withdrawal requested: {withdrawal_amount} SAR via {withdrawal_method}",
                        ip_address=self.get_client_ip(request),
                        success=True
                    )
                    
                    # Notify admin for approval
                    self.notify_admins_of_withdrawal(request.user, withdrawal_amount, withdrawal_method)
                    
                    messages.success(
                        request,
                        _('Withdrawal request submitted! Please wait for admin approval.')
                    )
                    
                    return redirect('wallet')
            
            except Exception as e:
                messages.error(request, str(e))
        
        return render(request, self.template_name, {
            'form': form,
            'page_title': _('Withdraw Funds'),
            'user': request.user,
        })
    
    def notify_admins_of_withdrawal(self, user, amount, method):
        """Notify admins about withdrawal request"""
        admins = User.objects.filter(
            user_type=User.UserType.ADMIN,
            is_active=True
        )
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type=Notification.NotificationType.PAYMENT,
                title='New Withdrawal Request',
                message=f'{user.get_full_name()} has requested a withdrawal of {amount} SAR via {method}.',
                action_url=reverse_lazy('admin_withdrawal_review')
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TransactionHistoryView(LoginRequiredMixin, ListView):
    """Transaction history view"""
    
    template_name = 'accounts/financial/transaction_history.html'
    context_object_name = 'transactions'
    paginate_by = 50
    
    def get_queryset(self):
        user = self.request.user
        
        queryset = Transaction.objects.filter(user=user)
        
        # Apply filters
        transaction_type = self.request.GET.get('transaction_type')
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        user = self.request.user
        total_deposits = Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            status=Transaction.Status.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_withdrawals = Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            status=Transaction.Status.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        total_bookings = Transaction.objects.filter(
            user=user,
            transaction_type=Transaction.TransactionType.BOOKING,
            status=Transaction.Status.COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context.update({
            'page_title': _('Transaction History'),
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'total_bookings': total_bookings,
            'transaction_type_choices': Transaction.TransactionType.choices,
            'status_choices': Transaction.Status.choices,
        })
        
        return context


class PaymentView(LoginRequiredMixin, CreateView):
    """Payment view for invoices"""
    
    template_name = 'accounts/financial/payment.html'
    form_class = PaymentForm
    success_url = reverse_lazy('invoice_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['invoice'] = self.get_invoice()
        return kwargs
    
    def get_invoice(self):
        invoice_id = self.request.GET.get('invoice_id')
        if invoice_id:
            try:
                return Invoice.objects.get(
                    pk=invoice_id,
                    user=self.request.user
                )
            except Invoice.DoesNotExist:
                return None
        return None
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                payment = form.save()
                invoice = self.get_invoice()
                
                if invoice:
                    # Update invoice payment
                    invoice.paid_amount = F('paid_amount') + payment.amount
                    invoice.save()
                    invoice.refresh_from_db()
                    
                    # Update invoice status
                    invoice.update_payment_status()
                    
                    # Link payment to invoice
                    payment.metadata = {
                        'invoice_id': str(invoice.id),
                        'invoice_number': invoice.invoice_number
                    }
                    payment.save()
                
                # If payment is from wallet, process immediately
                if payment.payment_method == Payment.PaymentMethod.WALLET:
                    payment.status = Payment.PaymentStatus.SUCCESS
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    # Create transaction
                    Transaction.objects.create(
                        user=self.request.user,
                        transaction_type=Transaction.TransactionType.PAYMENT,
                        amount=-payment.amount,
                        currency='SAR',
                        status=Transaction.Status.COMPLETED,
                        description=f'Payment for invoice {invoice.invoice_number if invoice else "general"}',
                        balance_before=self.request.user.wallet_balance,
                        balance_after=self.request.user.wallet_balance - payment.amount,
                        metadata={
                            'payment_id': payment.payment_id,
                            'invoice_id': str(invoice.id) if invoice else None
                        }
                    )
                    
                    # Update user wallet
                    self.request.user.wallet_balance = F('wallet_balance') - payment.amount
                    self.request.user.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=self.request.user,
                    activity_type=UserActivityLog.ActivityType.PAYMENT,
                    description=f"Payment made: {payment.amount} SAR via {payment.payment_method}",
                    ip_address=self.get_client_ip(),
                    success=True
                )
                
                messages.success(
                    self.request,
                    _('Payment submitted successfully!')
                )
                
                return redirect(self.success_url)
        
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.get_invoice()
        
        context.update({
            'page_title': _('Make Payment'),
            'invoice': invoice,
            'user': self.request.user,
        })
        
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class InvoiceListView(LoginRequiredMixin, ListView):
    """Invoice list view"""
    
    template_name = 'accounts/financial/invoices.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            # Admin can see all invoices
            queryset = Invoice.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            # Super agent can see invoices from their sub-agents
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            queryset = Invoice.objects.filter(user__in=sub_agents)
        else:
            # Regular users can only see their own invoices
            queryset = Invoice.objects.filter(user=user)
        
        # Apply filters
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(issue_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(issue_date__lte=date_to)
        
        return queryset.order_by('-issue_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        user = self.request.user
        total_invoices = self.get_queryset().count()
        total_outstanding = self.get_queryset().filter(
            status__in=['issued', 'overdue', 'partial_paid']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        overdue_invoices = self.get_queryset().filter(
            status='overdue'
        ).count()
        
        context.update({
            'page_title': _('Invoices'),
            'total_invoices': total_invoices,
            'total_outstanding': total_outstanding,
            'overdue_invoices': overdue_invoices,
            'status_choices': Invoice.InvoiceStatus.choices,
        })
        
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """Invoice detail view"""
    
    template_name = 'accounts/financial/invoice_detail.html'
    model = Invoice
    context_object_name = 'invoice'
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            return Invoice.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            return Invoice.objects.filter(user__in=sub_agents)
        else:
            return Invoice.objects.filter(user=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Invoice Details')
        return context


class CommissionView(LoginRequiredMixin, ListView):
    """Commission view"""
    
    template_name = 'accounts/financial/commission.html'
    context_object_name = 'commissions'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.ADMIN:
            # Admin can see all commissions
            queryset = CommissionTransaction.objects.all()
        elif user.user_type == User.UserType.SUPER_AGENT:
            # Super agent can see commissions from their sub-agents
            sub_agents = User.objects.filter(
                parent_hierarchy__parent_agent=user,
                parent_hierarchy__is_active=True
            )
            queryset = CommissionTransaction.objects.filter(agent__in=sub_agents)
        else:
            # Regular users can only see their own commissions
            queryset = CommissionTransaction.objects.filter(agent=user)
        
        # Apply filters
        status = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get commission statistics
        total_commission = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        pending_commission = self.get_queryset().filter(
            status='pending'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        paid_commission = self.get_queryset().filter(
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get user's commission rate
        commission_rate = user.commission_rate
        
        context.update({
            'page_title': _('Commissions'),
            'total_commission': total_commission,
            'pending_commission': pending_commission,
            'paid_commission': paid_commission,
            'commission_rate': commission_rate,
            'status_choices': CommissionTransaction.CommissionStatus.choices,
        })
        
        return context


class RefundRequestView(LoginRequiredMixin, CreateView):
    """Refund request view"""
    
    template_name = 'accounts/financial/refund_request.html'
    form_class = RefundRequestForm
    success_url = reverse_lazy('wallet')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Get booking from query params
        booking_id = self.request.GET.get('booking_id')
        booking_type = self.request.GET.get('booking_type')
        
        if booking_id and booking_type:
            if booking_type == 'flight':
                from ..models import FlightBooking
                try:
                    kwargs['booking'] = FlightBooking.objects.get(
                        booking_id=booking_id,
                        agent=self.request.user
                    )
                except FlightBooking.DoesNotExist:
                    pass
            
            elif booking_type == 'hotel':
                from ..models import HotelBooking
                try:
                    kwargs['booking'] = HotelBooking.objects.get(
                        booking_id=booking_id,
                        agent=self.request.user
                    )
                except HotelBooking.DoesNotExist:
                    pass
        
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                refund = form.save(commit=False)
                refund.user = self.request.user
                refund.requested_by = self.request.user
                refund.save()
                
                # Log activity
                UserActivityLog.objects.create(
                    user=self.request.user,
                    activity_type=UserActivityLog.ActivityType.REFUND,
                    description=f"Refund requested: {refund.refund_amount} SAR",
                    ip_address=self.get_client_ip(),
                    success=True
                )
                
                # Notify admin
                self.notify_admins_of_refund(refund)
                
                messages.success(
                    self.request,
                    _('Refund request submitted successfully!')
                )
                
                return redirect(self.success_url)
        
        except Exception as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
    
    def notify_admins_of_refund(self, refund):
        """Notify admins about refund request"""
        admins = User.objects.filter(
            user_type=User.UserType.ADMIN,
            is_active=True
        )
        
        for admin in admins:
            Notification.objects.create(
                user=admin,
                notification_type=Notification.NotificationType.REFUND,
                title='New Refund Request',
                message=f'{refund.user.get_full_name()} has requested a refund of {refund.refund_amount} SAR.',
                action_url=reverse_lazy('admin_refund_review')
            )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Request Refund')
        return context
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip