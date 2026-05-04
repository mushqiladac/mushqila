from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from ..models import TicketSale, Airline, PaymentMethod
from ..models.user import FinanceUser
from ..serializers import (
    TicketSaleSerializer, 
    TicketSaleCreateSerializer,
    AirlineSerializer,
    PaymentMethodSerializer
)


class TicketSaleViewSet(viewsets.ModelViewSet):
    """Ticket Sale API Endpoints for Flutter Mobile App"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSaleSerializer
    
    def get_queryset(self):
        """Filter tickets based on user role"""
        user = self.request.user
        if user.user_type == FinanceUser.UserType.MANAGER:
            return TicketSale.objects.all().select_related('user', 'airline', 'payment_method')
        else:
            return TicketSale.objects.filter(user=user).select_related('airline', 'payment_method')
    
    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == 'create':
            return TicketSaleCreateSerializer
        return TicketSaleSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new ticket sale"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            ticket_sale = serializer.save(user=request.user)
            
            # Create transaction record
            FinanceTransaction.objects.create(
                user=request.user,
                ticket_sale=ticket_sale,
                transaction_type=FinanceTransaction.TransactionType.SALE,
                amount=ticket_sale.total_amount,
                balance_before=request.user.current_balance,
                balance_after=request.user.current_balance + ticket_sale.commission_amount,
                description=f"Ticket sale - {ticket_sale.ticket_number}"
            )
            
            # Update user stats
            request.user.total_sales += ticket_sale.total_amount
            request.user.current_balance += ticket_sale.commission_amount
            request.user.save()
            
            return Response({
                'success': True,
                'message': 'Ticket sale created successfully',
                'data': TicketSaleSerializer(ticket_sale).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Failed to create ticket sale',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-sales')
    def my_sales(self, request):
        """Get current user's sales"""
        tickets = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(tickets, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='pending-approval')
    def pending_approval(self, request):
        """Get tickets pending approval (for managers)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        tickets = TicketSale.objects.filter(status=TicketSale.SaleStatus.PENDING)
        serializer = self.get_serializer(tickets, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='sales-summary')
    def sales_summary(self, request):
        """Get sales summary for dashboard"""
        user = request.user
        today = timezone.now().date()
        
        # Date filters
        date_filter = request.GET.get('filter', 'today')
        if date_filter == 'week':
            start_date = today - timedelta(days=7)
        elif date_filter == 'month':
            start_date = today - timedelta(days=30)
        else:
            start_date = today
        
        queryset = TicketSale.objects.filter(user=user, created_at__date__gte=start_date)
        
        # Calculate statistics
        total_sales = queryset.aggregate(
            total_amount=Sum('total_amount'),
            total_commission=Sum('commission_amount'),
            total_count=Count('id')
        )
        
        # Status breakdown
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Payment method breakdown
        payment_counts = queryset.values('payment_method__name').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        ).order_by('-total')
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_amount': total_sales['total_amount'] or 0,
                    'total_commission': total_sales['total_commission'] or 0,
                    'total_count': total_sales['total_count'] or 0
                },
                'status_breakdown': list(status_counts),
                'payment_breakdown': list(payment_counts),
                'filter': date_filter
            }
        })
    
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """Search tickets by PNR, ticket number, or passenger name"""
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({
                'success': False,
                'message': 'Search query required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(
            Q(pnr__icontains=query) |
            Q(ticket_number__icontains=query) |
            Q(passenger_name__icontains=query)
        )
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve ticket sale (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        ticket = self.get_object()
        ticket.status = TicketSale.SaleStatus.APPROVED
        ticket.save()
        
        # Create notification for user
        FinanceNotification.objects.create(
            user=ticket.user,
            notification_type=FinanceNotification.NotificationType.APPROVAL,
            title='Ticket Sale Approved',
            message=f'Your ticket sale {ticket.ticket_number} has been approved.',
            ticket_sale=ticket
        )
        
        return Response({
            'success': True,
            'message': 'Ticket sale approved successfully',
            'data': TicketSaleSerializer(ticket).data
        })
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject ticket sale (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        ticket = self.get_object()
        reason = request.data.get('reason', '')
        
        ticket.status = TicketSale.SaleStatus.REJECTED
        ticket.save()
        
        # Create notification for user
        FinanceNotification.objects.create(
            user=ticket.user,
            notification_type=FinanceNotification.NotificationType.REJECTION,
            title='Ticket Sale Rejected',
            message=f'Your ticket sale {ticket.ticket_number} has been rejected. Reason: {reason}',
            ticket_sale=ticket
        )
        
        return Response({
            'success': True,
            'message': 'Ticket sale rejected successfully',
            'data': TicketSaleSerializer(ticket).data
        })


class AirlineViewSet(viewsets.ReadOnlyModelViewSet):
    """Airline API Endpoints"""
    
    queryset = Airline.objects.filter(is_active=True)
    serializer_class = AirlineSerializer
    permission_classes = [IsAuthenticated]


class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """Payment Method API Endpoints"""
    
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
