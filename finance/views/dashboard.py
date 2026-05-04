from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, date
from ..models import TicketSale, FinanceTransaction, CreditSale, FinanceNotification
from ..models.user import FinanceUser
from ..serializers import DashboardSerializer


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard API Endpoints for Flutter Mobile App"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='overview')
    def overview(self, request):
        """Get dashboard overview data"""
        user = request.user
        today = timezone.now().date()
        
        # Date ranges
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        week_start = today - timedelta(days=7)
        month_start = today - timedelta(days=30)
        
        # Base queryset
        if user.user_type == FinanceUser.UserType.MANAGER:
            ticket_queryset = TicketSale.objects.all()
            user_queryset = FinanceUser.objects.all()
        else:
            ticket_queryset = TicketSale.objects.filter(user=user)
            user_queryset = FinanceUser.objects.filter(id=user.id)
        
        # Today's stats
        today_stats = ticket_queryset.filter(created_at__gte=today_start).aggregate(
            total_sales=Sum('total_amount'),
            total_commission=Sum('commission_amount'),
            total_tickets=Count('id'),
            avg_ticket_price=Avg('total_amount')
        )
        
        # Week stats
        week_stats = ticket_queryset.filter(created_at__gte=week_start).aggregate(
            total_sales=Sum('total_amount'),
            total_commission=Sum('commission_amount'),
            total_tickets=Count('id')
        )
        
        # Month stats
        month_stats = ticket_queryset.filter(created_at__gte=month_start).aggregate(
            total_sales=Sum('total_amount'),
            total_commission=Sum('commission_amount'),
            total_tickets=Count('id')
        )
        
        # Status breakdown
        status_breakdown = ticket_queryset.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('status')
        
        # Payment method breakdown
        payment_breakdown = ticket_queryset.values('payment_method__name').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('-total_amount')
        
        # Recent activity
        recent_tickets = ticket_queryset.order_by('-created_at')[:5]
        
        # Credit sales info
        credit_info = CreditSale.objects.filter(
            ticket_sale__in=ticket_queryset
        ).aggregate(
            total_credit=Sum('total_amount'),
            total_paid=Sum('paid_amount'),
            total_remaining=Sum('remaining_amount'),
            overdue_count=Count('id', filter=Q(due_date__lt=today, payment_status__in=['pending', 'partial']))
        )
        
        data = {
            'user_info': {
                'name': user.get_full_name(),
                'email': user.email,
                'user_type': user.user_type,
                'current_balance': float(user.current_balance),
                'total_sales': float(user.total_sales)
            },
            'statistics': {
                'today': {
                    'total_sales': float(today_stats['total_sales'] or 0),
                    'total_commission': float(today_stats['total_commission'] or 0),
                    'total_tickets': today_stats['total_tickets'] or 0,
                    'avg_ticket_price': float(today_stats['avg_ticket_price'] or 0)
                },
                'week': {
                    'total_sales': float(week_stats['total_sales'] or 0),
                    'total_commission': float(week_stats['total_commission'] or 0),
                    'total_tickets': week_stats['total_tickets'] or 0
                },
                'month': {
                    'total_sales': float(month_stats['total_sales'] or 0),
                    'total_commission': float(month_stats['total_commission'] or 0),
                    'total_tickets': month_stats['total_tickets'] or 0
                }
            },
            'breakdowns': {
                'status': list(status_breakdown),
                'payment_methods': list(payment_breakdown)
            },
            'credit_info': {
                'total_credit': float(credit_info['total_credit'] or 0),
                'total_paid': float(credit_info['total_paid'] or 0),
                'total_remaining': float(credit_info['total_remaining'] or 0),
                'overdue_count': credit_info['overdue_count'] or 0
            },
            'recent_activity': [
                {
                    'id': ticket.id,
                    'ticket_number': ticket.ticket_number,
                    'passenger_name': ticket.passenger_name,
                    'total_amount': float(ticket.total_amount),
                    'status': ticket.status,
                    'created_at': ticket.created_at.isoformat()
                }
                for ticket in recent_tickets
            ]
        }
        
        return Response({
            'success': True,
            'data': data
        })
    
    @action(detail=False, methods=['get'], url_path='sales-chart')
    def sales_chart(self, request):
        """Get sales data for charts"""
        user = request.user
        period = request.GET.get('period', 'week')
        
        # Date range
        if period == 'day':
            days = 1
        elif period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        else:
            days = 7
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset
        if user.user_type == FinanceUser.UserType.MANAGER:
            queryset = TicketSale.objects.filter(created_at__date__gte=start_date)
        else:
            queryset = TicketSale.objects.filter(user=user, created_at__date__gte=start_date)
        
        # Daily sales data
        daily_data = []
        for i in range(days + 1):
            current_date = start_date + timedelta(days=i)
            day_stats = queryset.filter(created_at__date=current_date).aggregate(
                total_sales=Sum('total_amount'),
                total_commission=Sum('commission_amount'),
                ticket_count=Count('id')
            )
            
            daily_data.append({
                'date': current_date.isoformat(),
                'total_sales': float(day_stats['total_sales'] or 0),
                'total_commission': float(day_stats['total_commission'] or 0),
                'ticket_count': day_stats['ticket_count'] or 0
            })
        
        return Response({
            'success': True,
            'data': {
                'period': period,
                'daily_data': daily_data
            }
        })
    
    @action(detail=False, methods=['get'], url_path='top-performers')
    def top_performers(self, request):
        """Get top performers (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        period = request.GET.get('period', 'month')
        
        # Date range
        if period == 'day':
            days = 1
        elif period == 'week':
            days = 7
        else:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Top users by sales
        top_users = FinanceUser.objects.filter(
            ticket_sales__created_at__date__gte=start_date
        ).annotate(
            total_sales=Sum('ticket_sales__total_amount'),
            total_tickets=Count('ticket_sales'),
            total_commission=Sum('ticket_sales__commission_amount')
        ).order_by('-total_sales')[:10]
        
        data = [
            {
                'user_id': user.id,
                'name': user.get_full_name(),
                'email': user.email,
                'total_sales': float(user.total_sales or 0),
                'total_tickets': user.total_tickets or 0,
                'total_commission': float(user.total_commission or 0)
            }
            for user in top_users
        ]
        
        return Response({
            'success': True,
            'data': data
        })
    
    @action(detail=False, methods=['get'], url_path='pending-tasks')
    def pending_tasks(self, request):
        """Get pending tasks for user"""
        user = request.user
        tasks = []
        
        if user.user_type == FinanceUser.UserType.MANAGER:
            # Pending approvals
            pending_tickets = TicketSale.objects.filter(status=TicketSale.SaleStatus.PENDING).count()
            if pending_tickets > 0:
                tasks.append({
                    'type': 'approval',
                    'title': 'Pending Ticket Approvals',
                    'count': pending_tickets,
                    'priority': 'high'
                })
            
            # Overdue payments
            overdue_count = CreditSale.objects.filter(
                due_date__lt=timezone.now().date(),
                payment_status__in=['pending', 'partial']
            ).count()
            if overdue_count > 0:
                tasks.append({
                    'type': 'overdue',
                    'title': 'Overdue Payments',
                    'count': overdue_count,
                    'priority': 'medium'
                })
        else:
            # User's pending submissions
            pending_count = TicketSale.objects.filter(
                user=user,
                status=TicketSale.SaleStatus.PENDING
            ).count()
            if pending_count > 0:
                tasks.append({
                    'type': 'pending',
                    'title': 'Pending Submissions',
                    'count': pending_count,
                    'priority': 'high'
                })
            
            # User's overdue payments
            overdue_count = CreditSale.objects.filter(
                user=user,
                due_date__lt=timezone.now().date(),
                payment_status__in=['pending', 'partial']
            ).count()
            if overdue_count > 0:
                tasks.append({
                    'type': 'payment_due',
                    'title': 'Payments Due',
                    'count': overdue_count,
                    'priority': 'high'
                })
        
        return Response({
            'success': True,
            'data': tasks
        })
    
    @action(detail=False, methods=['get'], url_path='notifications')
    def notifications(self, request):
        """Get user notifications"""
        user = request.user
        limit = int(request.GET.get('limit', 20))
        
        notifications = FinanceNotification.objects.filter(
            user=user
        ).order_by('-created_at')[:limit]
        
        data = [
            {
                'id': notif.id,
                'type': notif.notification_type,
                'title': notif.get_title(),
                'message': notif.get_message(),
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'action_url': notif.action_url,
                'action_text': notif.get_action_text()
            }
            for notif in notifications
        ]
        
        return Response({
            'success': True,
            'data': data
        })
    
    @action(detail=False, methods=['post'], url_path='mark-notification-read')
    def mark_notification_read(self, request):
        """Mark notification as read"""
        notification_id = request.data.get('notification_id')
        
        try:
            notification = FinanceNotification.objects.get(
                id=notification_id,
                user=request.user
            )
            notification.mark_as_read()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            })
        except FinanceNotification.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)
