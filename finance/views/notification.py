from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from ..models import FinanceNotification
from ..models.notification import NotificationTemplate
from ..models.user import FinanceUser
from ..serializers import (
    FinanceNotificationSerializer,
    NotificationTemplateSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """Notification API Endpoints for Flutter Mobile App"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = FinanceNotificationSerializer
    
    def get_queryset(self):
        """Filter notifications for current user"""
        return FinanceNotification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        """Get notification counts"""
        user = request.user
        
        counts = FinanceNotification.objects.filter(user=user).aggregate(
            total=Count('id'),
            unread=Count('id', filter=Q(is_read=False))
        )
        
        # Count by type
        type_counts = FinanceNotification.objects.filter(user=user).values('notification_type').annotate(
            count=Count('id')
        ).order_by('notification_type')
        
        return Response({
            'success': True,
            'data': {
                'total': counts['total'],
                'unread': counts['unread'],
                'by_type': list(type_counts)
            }
        })
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({
            'success': True,
            'message': 'Notification marked as read',
            'data': self.get_serializer(notification).data
        })
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        notifications = self.get_queryset().filter(is_read=False)
        count = notifications.count()
        
        notifications.update(is_read=True, read_at=timezone.now())
        
        return Response({
            'success': True,
            'message': f'{count} notifications marked as read'
        })
    
    @action(detail=True, methods=['delete'], url_path='delete')
    def delete_notification(self, request, pk=None):
        """Delete notification"""
        notification = self.get_object()
        notification.delete()
        
        return Response({
            'success': True,
            'message': 'Notification deleted successfully'
        })
    
    @action(detail=False, methods=['get'], url_path='by-type')
    def by_type(self, request):
        """Get notifications by type"""
        notification_type = request.GET.get('type')
        
        if not notification_type:
            return Response({
                'success': False,
                'message': 'Notification type required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        notifications = self.get_queryset().filter(notification_type=notification_type)
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='send-test')
    def send_test_notification(self, request):
        """Send test notification (for development)"""
        user = request.user
        
        notification = FinanceNotification.objects.create(
            user=user,
            notification_type=FinanceNotification.NotificationType.INFO,
            title='Test Notification',
            title_ar='اختبار إشعار',
            message='This is a test notification from the finance app.',
            message_ar='هذا إشعار اختبار من تطبيق المالية.',
            action_url='/dashboard',
            action_text='View Dashboard',
            action_text_ar='عرض لوحة القيادة'
        )
        
        return Response({
            'success': True,
            'message': 'Test notification sent',
            'data': self.get_serializer(notification).data
        }, status=status.HTTP_201_CREATED)


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """Notification Template API Endpoints (Admin only)"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationTemplateSerializer
    queryset = NotificationTemplate.objects.filter(is_active=True)
    
    def get_permissions(self):
        """Only admins can manage templates"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        """Send email using template"""
        if request.user.user_type != FinanceUser.UserType.ADMIN:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        template = self.get_object()
        recipient_email = request.data.get('email')
        context = request.data.get('context', {})
        language = request.data.get('language', 'en')
        
        if not recipient_email:
            return Response({
                'success': False,
                'message': 'Recipient email required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            
            # Render email content
            subject = template.get_subject(language)
            html_content = template.get_html_content(language)
            text_content = template.get_text_content(language)
            
            # Replace placeholders with context
            for key, value in context.items():
                placeholder = f'{{{{{key}}}}}'
                subject = subject.replace(placeholder, str(value))
                html_content = html_content.replace(placeholder, str(value))
                text_content = text_content.replace(placeholder, str(value))
            
            # Send email
            send_mail(
                subject,
                text_content,
                'noreply@mushqila.com',
                [recipient_email],
                html_message=html_content,
                fail_silently=False,
            )
            
            return Response({
                'success': True,
                'message': 'Email sent successfully'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='template-types')
    def template_types(self, request):
        """Get available template types"""
        template_types = [
            'welcome_email',
            'password_reset',
            'ticket_approved',
            'ticket_rejected',
            'payment_received',
            'payment_due',
            'account_suspended',
            'account_activated'
        ]
        
        return Response({
            'success': True,
            'data': template_types
        })
    
    @action(detail=False, methods=['post'], url_path='create-default-templates')
    def create_default_templates(self, request):
        """Create default notification templates"""
        if request.user.user_type != FinanceUser.UserType.ADMIN:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        default_templates = [
            {
                'template_type': 'welcome_email',
                'subject': 'Welcome to Finance App',
                'subject_ar': 'مرحبا بك في تطبيق المالية',
                'html_content': '<h1>Welcome {{name}}!</h1><p>Thank you for joining Finance App.</p>',
                'html_content_ar': '<h1>مرحبا {{name}}!</h1><p>شكرا لانضمامك إلى تطبيق المالية.</p>',
                'text_content': 'Welcome {{name}}! Thank you for joining Finance App.',
                'text_content_ar': 'مرحبا {{name}}! شكرا لانضمامك إلى تطبيق المالية.'
            },
            {
                'template_type': 'password_reset',
                'subject': 'Password Reset OTP',
                'subject_ar': 'OTP إعادة تعيين كلمة المرور',
                'html_content': '<h1>Password Reset</h1><p>Your OTP code is: {{otp_code}}</p>',
                'html_content_ar': '<h1>إعادة تعيين كلمة المرور</h1><p>رمز OTP الخاص بك هو: {{otp_code}}</p>',
                'text_content': 'Your OTP code is: {{otp_code}}',
                'text_content_ar': 'رمز OTP الخاص بك هو: {{otp_code}}'
            },
            {
                'template_type': 'ticket_approved',
                'subject': 'Ticket Sale Approved',
                'subject_ar': 'تمت الموافقة على بيع التذكرة',
                'html_content': '<h1>Ticket Approved</h1><p>Your ticket {{ticket_number}} has been approved.</p>',
                'html_content_ar': '<h1>تمت الموافقة على التذكرة</h1><p>تمت الموافقة على تذكرتك {{ticket_number}}.</p>',
                'text_content': 'Your ticket {{ticket_number}} has been approved.',
                'text_content_ar': 'تمت الموافقة على تذكرتك {{ticket_number}}.'
            },
            {
                'template_type': 'ticket_rejected',
                'subject': 'Ticket Sale Rejected',
                'subject_ar': 'تم رفض بيع التذكرة',
                'html_content': '<h1>Ticket Rejected</h1><p>Your ticket {{ticket_number}} has been rejected. Reason: {{reason}}</p>',
                'html_content_ar': '<h1>تم رفض التذكرة</h1><p>تم رفض تذكرتك {{ticket_number}}. السبب: {{reason}}</p>',
                'text_content': 'Your ticket {{ticket_number}} has been rejected. Reason: {{reason}}',
                'text_content_ar': 'تم رفض تذكرتك {{ticket_number}}. السبب: {{reason}}'
            }
        ]
        
        created_count = 0
        for template_data in default_templates:
            template, created = NotificationTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                created_count += 1
        
        return Response({
            'success': True,
            'message': f'Created {created_count} default templates',
            'data': {
                'created_count': created_count,
                'total_templates': len(default_templates)
            }
        })
