from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from ..models import FinanceTransaction, CreditSale
from ..models.transaction import PaymentInstallment
from ..models.user import FinanceUser
from ..serializers import (
    FinanceTransactionSerializer,
    CreditSaleSerializer,
    PaymentInstallmentSerializer
)


class TransactionViewSet(viewsets.ModelViewSet):
    """Transaction API Endpoints for Flutter Mobile App"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = FinanceTransactionSerializer
    
    def get_queryset(self):
        """Filter transactions based on user role"""
        user = self.request.user
        if user.user_type == FinanceUser.UserType.MANAGER:
            return FinanceTransaction.objects.all().select_related('user', 'ticket_sale')
        else:
            return FinanceTransaction.objects.filter(user=user).select_related('ticket_sale')
    
    @action(detail=False, methods=['get'], url_path='my-transactions')
    def my_transactions(self, request):
        """Get current user's transactions"""
        transactions = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(transactions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='transaction-summary')
    def transaction_summary(self, request):
        """Get transaction summary for dashboard"""
        user = request.user
        today = timezone.now().date()
        
        # Date filters
        date_filter = request.GET.get('filter', 'today')
        if date_filter == 'week':
            start_date = today - timezone.timedelta(days=7)
        elif date_filter == 'month':
            start_date = today - timezone.timedelta(days=30)
        else:
            start_date = today
        
        queryset = FinanceTransaction.objects.filter(
            user=user, 
            created_at__date__gte=start_date
        )
        
        # Calculate statistics by transaction type
        type_stats = queryset.values('transaction_type').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('transaction_type')
        
        # Status breakdown
        status_stats = queryset.values('status').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('status')
        
        # Total statistics
        total_stats = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id')
        )
        
        return Response({
            'success': True,
            'data': {
                'total': {
                    'total_amount': float(total_stats['total_amount'] or 0),
                    'total_count': total_stats['total_count'] or 0
                },
                'by_type': list(type_stats),
                'by_status': list(status_stats),
                'filter': date_filter
            }
        })
    
    @action(detail=False, methods=['get'], url_path='balance-history')
    def balance_history(self, request):
        """Get user balance history"""
        user = request.user
        days = int(request.GET.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        transactions = FinanceTransaction.objects.filter(
            user=user,
            created_at__date__gte=start_date
        ).order_by('created_at')
        
        balance_data = []
        running_balance = user.current_balance
        
        for transaction in reversed(transactions):
            balance_data.append({
                'date': transaction.created_at.isoformat(),
                'transaction_id': transaction.transaction_id,
                'transaction_type': transaction.transaction_type,
                'amount': float(transaction.amount),
                'balance_before': float(transaction.balance_before),
                'balance_after': float(transaction.balance_after),
                'description': transaction.description
            })
        
        return Response({
            'success': True,
            'data': {
                'current_balance': float(user.current_balance),
                'history': balance_data
            }
        })


class CreditSaleViewSet(viewsets.ModelViewSet):
    """Credit Sale API Endpoints for Flutter Mobile App"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = CreditSaleSerializer
    
    def get_queryset(self):
        """Filter credit sales based on user role"""
        user = self.request.user
        if user.user_type == FinanceUser.UserType.MANAGER:
            return CreditSale.objects.all().select_related('user', 'ticket_sale')
        else:
            return CreditSale.objects.filter(user=user).select_related('ticket_sale')
    
    @action(detail=False, methods=['get'], url_path='my-credits')
    def my_credits(self, request):
        """Get current user's credit sales"""
        credit_sales = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(credit_sales, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='overdue-payments')
    def overdue_payments(self, request):
        """Get overdue payments (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        overdue_credits = CreditSale.objects.filter(
            due_date__lt=timezone.now().date(),
            payment_status__in=['pending', 'partial']
        ).select_related('user', 'ticket_sale')
        
        serializer = self.get_serializer(overdue_credits, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='credit-summary')
    def credit_summary(self, request):
        """Get credit sales summary"""
        user = request.user
        
        # Base queryset
        if user.user_type == FinanceUser.UserType.MANAGER:
            queryset = CreditSale.objects.all()
        else:
            queryset = CreditSale.objects.filter(user=user)
        
        # Calculate statistics
        stats = queryset.aggregate(
            total_credit=Sum('total_amount'),
            total_paid=Sum('paid_amount'),
            total_remaining=Sum('remaining_amount'),
            overdue_count=Count('id', filter=Q(
                due_date__lt=timezone.now().date(),
                payment_status__in=['pending', 'partial']
            ))
        )
        
        # Status breakdown
        status_breakdown = queryset.values('payment_status').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('payment_status')
        
        # Upcoming payments (next 7 days)
        upcoming_date = timezone.now().date() + timezone.timedelta(days=7)
        upcoming_payments = queryset.filter(
            due_date__lte=upcoming_date,
            due_date__gte=timezone.now().date(),
            payment_status__in=['pending', 'partial']
        ).count()
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_credit': float(stats['total_credit'] or 0),
                    'total_paid': float(stats['total_paid'] or 0),
                    'total_remaining': float(stats['total_remaining'] or 0),
                    'overdue_count': stats['overdue_count'] or 0,
                    'upcoming_payments': upcoming_payments
                },
                'status_breakdown': list(status_breakdown)
            }
        })
    
    @action(detail=True, methods=['post'], url_path='make-payment')
    def make_payment(self, request, pk=None):
        """Make payment for credit sale"""
        credit_sale = self.get_object()
        
        # Only user can make their own payments
        if credit_sale.user != request.user:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        amount = request.data.get('amount')
        if not amount:
            return Response({
                'success': False,
                'message': 'Payment amount required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = float(amount)
            if amount <= 0 or amount > credit_sale.remaining_amount:
                return Response({
                    'success': False,
                    'message': 'Invalid payment amount'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid payment amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update credit sale
        credit_sale.paid_amount += amount
        credit_sale.last_payment_date = timezone.now().date()
        credit_sale.save()
        
        # Create transaction record
        FinanceTransaction.objects.create(
            user=request.user,
            ticket_sale=credit_sale.ticket_sale,
            transaction_type=FinanceTransaction.TransactionType.DEPOSIT,
            amount=amount,
            balance_before=request.user.current_balance,
            balance_after=request.user.current_balance,
            description=f"Payment for credit sale - {credit_sale.ticket_sale.ticket_number}"
        )
        
        # Create notification
        FinanceNotification.objects.create(
            user=request.user,
            notification_type=FinanceNotification.NotificationType.PAYMENT,
            title='Payment Received',
            message=f'Payment of {amount} SAR received for ticket {credit_sale.ticket_sale.ticket_number}',
            ticket_sale=credit_sale.ticket_sale
        )
        
        return Response({
            'success': True,
            'message': 'Payment processed successfully',
            'data': CreditSaleSerializer(credit_sale).data
        })
    
    @action(detail=True, methods=['get'], url_path='installments')
    def installments(self, request, pk=None):
        """Get payment installments for credit sale"""
        credit_sale = self.get_object()
        
        installments = credit_sale.installments.all().order_by('installment_number')
        serializer = PaymentInstallmentSerializer(installments, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='add-installment')
    def add_installment(self, request, pk=None):
        """Add payment installment (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        credit_sale = self.get_object()
        
        installment_number = request.data.get('installment_number')
        amount = request.data.get('amount')
        due_date = request.data.get('due_date')
        
        if not all([installment_number, amount, due_date]):
            return Response({
                'success': False,
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            installment = PaymentInstallment.objects.create(
                credit_sale=credit_sale,
                installment_number=installment_number,
                amount=amount,
                due_date=due_date
            )
            
            return Response({
                'success': True,
                'message': 'Installment added successfully',
                'data': PaymentInstallmentSerializer(installment).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to add installment'
            }, status=status.HTTP_400_BAD_REQUEST)
