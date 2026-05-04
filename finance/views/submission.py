from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from ..models import SalesSubmission
from ..models.submission import SubmissionComment
from ..models.user import FinanceUser
from ..models.ticket import TicketSale
from ..serializers import (
    SalesSubmissionSerializer,
    SalesSubmissionCreateSerializer,
    SubmissionCommentSerializer
)


class SubmissionViewSet(viewsets.ModelViewSet):
    """Sales Submission API Endpoints for Flutter Mobile App"""
    
    permission_classes = [IsAuthenticated]
    serializer_class = SalesSubmissionSerializer
    
    def get_queryset(self):
        """Filter submissions based on user role"""
        user = self.request.user
        if user.user_type == FinanceUser.UserType.MANANAGER:
            return SalesSubmission.objects.all().select_related('user', 'ticket_sale', 'reviewed_by')
        else:
            return SalesSubmission.objects.filter(user=user).select_related('ticket_sale', 'reviewed_by')
    
    def get_serializer_class(self):
        """Return different serializers for different actions"""
        if self.action == 'create':
            return SalesSubmissionCreateSerializer
        return SalesSubmissionSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new sales submission"""
        ticket_sale_id = request.data.get('ticket_sale_id')
        
        try:
            ticket_sale = TicketSale.objects.get(id=ticket_sale_id, user=request.user)
        except TicketSale.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Ticket sale not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if submission already exists
        if SalesSubmission.objects.filter(ticket_sale=ticket_sale).exists():
            return Response({
                'success': False,
                'message': 'Submission already exists for this ticket'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create submission
        submission = SalesSubmission.objects.create(
            user=request.user,
            ticket_sale=ticket_sale
        )
        
        # Update ticket sale status
        ticket_sale.status = TicketSale.SaleStatus.PENDING
        ticket_sale.save()
        
        # Create notification for managers
        managers = FinanceUser.objects.filter(user_type=FinanceUser.UserType.MANAGER)
        for manager in managers:
            FinanceNotification.objects.create(
                user=manager,
                notification_type=FinanceNotification.NotificationType.SUBMISSION,
                title='New Ticket Submission',
                message=f'New ticket submission from {request.user.get_full_name()} - {ticket_sale.ticket_number}',
                ticket_sale=ticket_sale,
                submission=submission
            )
        
        return Response({
            'success': True,
            'message': 'Submission created successfully',
            'data': SalesSubmissionSerializer(submission).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='my-submissions')
    def my_submissions(self, request):
        """Get current user's submissions"""
        submissions = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(submissions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='pending-review')
    def pending_review(self, request):
        """Get submissions pending review (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        submissions = SalesSubmission.objects.filter(status=SalesSubmission.SubmissionStatus.PENDING)
        serializer = self.get_serializer(submissions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve submission (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        submission = self.get_object()
        notes = request.data.get('notes', '')
        
        submission.approve(reviewer=request.user, notes=notes)
        
        # Create notification for user
        FinanceNotification.objects.create(
            user=submission.user,
            notification_type=FinanceNotification.NotificationType.APPROVAL,
            title='Submission Approved',
            message=f'Your submission for ticket {submission.ticket_sale.ticket_number} has been approved',
            ticket_sale=submission.ticket_sale,
            submission=submission
        )
        
        return Response({
            'success': True,
            'message': 'Submission approved successfully',
            'data': SalesSubmissionSerializer(submission).data
        })
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject submission (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        submission = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        submission.reject(reviewer=request.user, reason=reason)
        
        # Create notification for user
        FinanceNotification.objects.create(
            user=submission.user,
            notification_type=FinanceNotification.NotificationType.REJECTION,
            title='Submission Rejected',
            message=f'Your submission for ticket {submission.ticket_sale.ticket_number} has been rejected. Reason: {reason}',
            ticket_sale=submission.ticket_sale,
            submission=submission
        )
        
        return Response({
            'success': True,
            'message': 'Submission rejected successfully',
            'data': SalesSubmissionSerializer(submission).data
        })
    
    @action(detail=True, methods=['post'], url_path='request-revision')
    def request_revision(self, request, pk=None):
        """Request revision for submission (manager only)"""
        if request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        submission = self.get_object()
        notes = request.data.get('notes', '')
        
        if not notes:
            return Response({
                'success': False,
                'message': 'Revision notes are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        submission.request_revision(reviewer=request.user, notes=notes)
        
        # Create notification for user
        FinanceNotification.objects.create(
            user=submission.user,
            notification_type=FinanceNotification.NotificationType.SUBMISSION,
            title='Revision Required',
            message=f'Your submission for ticket {submission.ticket_sale.ticket_number} requires revision',
            ticket_sale=submission.ticket_sale,
            submission=submission
        )
        
        return Response({
            'success': True,
            'message': 'Revision requested successfully',
            'data': SalesSubmissionSerializer(submission).data
        })
    
    @action(detail=True, methods=['post'], url_path='resubmit')
    def resubmit(self, request, pk=None):
        """Resubmit after revision"""
        submission = self.get_object()
        
        # Only submission owner can resubmit
        if submission.user != request.user:
            return Response({
                'success': False,
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if revision is required
        if not submission.needs_revision:
            return Response({
                'success': False,
                'message': 'This submission does not require revision'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        response = request.data.get('response', '')
        submission.resubmit(response=response)
        
        # Create notification for reviewer
        if submission.reviewed_by:
            FinanceNotification.objects.create(
                user=submission.reviewed_by,
                notification_type=FinanceNotification.NotificationType.SUBMISSION,
                title='Submission Resubmitted',
                message=f'{request.user.get_full_name()} has resubmitted ticket {submission.ticket_sale.ticket_number}',
                ticket_sale=submission.ticket_sale,
                submission=submission
            )
        
        return Response({
            'success': True,
            'message': 'Submission resubmitted successfully',
            'data': SalesSubmissionSerializer(submission).data
        })
    
    @action(detail=True, methods=['get'], url_path='comments')
    def comments(self, request, pk=None):
        """Get comments for submission"""
        submission = self.get_object()
        
        # Filter internal comments based on user role
        if request.user.user_type == FinanceUser.UserType.MANANAGER:
            comments = submission.comments.all()
        else:
            comments = submission.comments.filter(is_internal=False)
        
        serializer = SubmissionCommentSerializer(comments, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='add-comment')
    def add_comment(self, request, pk=None):
        """Add comment to submission"""
        submission = self.get_object()
        
        comment_text = request.data.get('comment', '')
        is_internal = request.data.get('is_internal', False)
        
        if not comment_text:
            return Response({
                'success': False,
                'message': 'Comment text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Only managers can add internal comments
        if is_internal and request.user.user_type != FinanceUser.UserType.MANAGER:
            return Response({
                'success': False,
                'message': 'Only managers can add internal comments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        comment = SubmissionComment.objects.create(
            submission=submission,
            author=request.user,
            comment=comment_text,
            is_internal=is_internal
        )
        
        return Response({
            'success': True,
            'message': 'Comment added successfully',
            'data': SubmissionCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='submission-stats')
    def submission_stats(self, request):
        """Get submission statistics"""
        user = request.user
        
        # Base queryset
        if user.user_type == FinanceUser.UserType.MANAGER:
            queryset = SalesSubmission.objects.all()
        else:
            queryset = SalesSubmission.objects.filter(user=user)
        
        # Status breakdown
        status_stats = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Recent activity
        recent_submissions = queryset.order_by('-submitted_at')[:5]
        
        # Calculate approval rate
        total_submissions = queryset.count()
        approved_submissions = queryset.filter(status=SalesSubmission.SubmissionStatus.APPROVED).count()
        approval_rate = (approved_submissions / total_submissions * 100) if total_submissions > 0 else 0
        
        return Response({
            'success': True,
            'data': {
                'status_breakdown': list(status_stats),
                'total_submissions': total_submissions,
                'approved_submissions': approved_submissions,
                'approval_rate': round(approval_rate, 2),
                'recent_submissions': [
                    {
                        'id': sub.id,
                        'ticket_number': sub.ticket_sale.ticket_number,
                        'status': sub.status,
                        'submitted_at': sub.submitted_at.isoformat()
                    }
                    for sub in recent_submissions
                ]
            }
        })
    
    @action(detail=False, methods=['get'], url_path='submission-history')
    def submission_history(self, request):
        """Get submission history for charts"""
        user = request.user
        days = int(request.GET.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        # Base queryset
        if user.user_type == FinanceUser.UserType.MANAGER:
            queryset = SalesSubmission.objects.filter(submitted_at__date__gte=start_date)
        else:
            queryset = SalesSubmission.objects.filter(
                user=user,
                submitted_at__date__gte=start_date
            )
        
        # Daily submission data
        daily_data = []
        for i in range(days + 1):
            current_date = start_date + timezone.timedelta(days=i)
            day_stats = queryset.filter(submitted_at__date=current_date).aggregate(
                total_submissions=Count('id'),
                approved=Count('id', filter=Q(status=SalesSubmission.SubmissionStatus.APPROVED)),
                rejected=Count('id', filter=Q(status=SalesSubmission.SubmissionStatus.REJECTED)),
                pending=Count('id', filter=Q(status=SalesSubmission.SubmissionStatus.PENDING))
            )
            
            daily_data.append({
                'date': current_date.isoformat(),
                'total_submissions': day_stats['total_submissions'] or 0,
                'approved': day_stats['approved'] or 0,
                'rejected': day_stats['rejected'] or 0,
                'pending': day_stats['pending'] or 0
            })
        
        return Response({
            'success': True,
            'data': {
                'daily_data': daily_data
            }
        })
