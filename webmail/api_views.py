from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404

from .models import EmailAccount, Email, EmailAttachment, Contact
from .api_serializers import (
    EmailAccountSerializer, EmailListSerializer, EmailDetailSerializer,
    EmailSendSerializer, EmailDraftSerializer, ContactSerializer,
    LoginSerializer, ChangePasswordSerializer, ForgotPasswordSerializer,
    ResetPasswordSerializer, EmailStatsSerializer, UserSerializer
)
from .services import EmailService


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsEmailAccountOwner(permissions.BasePermission):
    """Custom permission to only allow owners of an email account to access it"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user owns the email account
        if hasattr(obj, 'account'):
            return obj.account.user == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


# ============================================================================
# Authentication Views
# ============================================================================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """Login with email and password"""
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    try:
        account = EmailAccount.objects.get(email_address=email, is_active=True)
        
        if not account.check_password(password):
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(account.user)
        
        return Response({
            'success': True,
            'data': {
                'token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(account.user).data,
                'account': EmailAccountSerializer(account).data
            }
        }, status=status.HTTP_200_OK)
        
    except EmailAccount.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid email or password'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout user"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 'LOGOUT_ERROR',
                'message': str(e)
            }
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password_view(request):
    """Request password reset"""
    serializer = ForgotPasswordSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    try:
        account = EmailAccount.objects.get(email_address=email, is_active=True)
        
        if not account.alternate_email:
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_ALTERNATE_EMAIL',
                    'message': 'No alternate email found for this account'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate reset token
        token = account.generate_reset_token()
        
        # Send email (implement email sending logic)
        # For now, return success
        
        return Response({
            'success': True,
            'message': 'Temporary password sent to alternate email'
        }, status=status.HTTP_200_OK)
        
    except EmailAccount.DoesNotExist:
        # Don't reveal if email exists or not
        return Response({
            'success': True,
            'message': 'If the email exists, a temporary password has been sent'
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password_view(request):
    """Reset password with temporary password"""
    serializer = ResetPasswordSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    temporary_password = serializer.validated_data['temporary_password']
    new_password = serializer.validated_data['new_password']
    
    try:
        account = EmailAccount.objects.get(email_address=email, is_active=True)
        
        if not account.is_reset_token_valid(temporary_password):
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired temporary password'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        account.set_password(new_password)
        account.user.set_password(new_password)
        account.user.save()
        account.clear_reset_token()
        
        return Response({
            'success': True,
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)
        
    except EmailAccount.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_EMAIL',
                'message': 'Invalid email address'
            }
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """Change password"""
    serializer = ChangePasswordSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    
    if not account:
        return Response({
            'success': False,
            'error': {
                'code': 'NO_ACCOUNT',
                'message': 'No email account found'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']
    
    if not account.check_password(current_password):
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_PASSWORD',
                'message': 'Current password is incorrect'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update passwords
    account.set_password(new_password)
    account.user.set_password(new_password)
    account.user.save()
    account.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)


# ============================================================================
# Email Views
# ============================================================================

class EmailViewSet(viewsets.ModelViewSet):
    """ViewSet for Email operations"""
    permission_classes = [IsEmailAccountOwner]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmailListSerializer
        elif self.action in ['send', 'create']:
            return EmailSendSerializer
        elif self.action == 'draft':
            return EmailDraftSerializer
        return EmailDetailSerializer
    
    def get_queryset(self):
        account = EmailAccount.objects.filter(user=self.request.user, is_active=True).first()
        if not account:
            return Email.objects.none()
        
        queryset = Email.objects.filter(account=account)
        
        # Filter by folder
        folder = self.request.query_params.get('folder', 'inbox')
        queryset = queryset.filter(folder=folder)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by starred
        is_starred = self.request.query_params.get('is_starred')
        if is_starred is not None:
            queryset = queryset.filter(is_starred=is_starred.lower() == 'true')
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-received_at')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List emails"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': self.paginator.get_paginated_response(serializer.data).data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get email detail"""
        instance = self.get_object()
        
        # Mark as read
        if not instance.is_read:
            instance.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Send email"""
        serializer = EmailSendSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
        
        if not account:
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_ACCOUNT',
                    'message': 'No email account found'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Send email using EmailService
        email_service = EmailService(account)
        result = email_service.send_email(
            to_addresses=serializer.validated_data['to_addresses'],
            subject=serializer.validated_data['subject'],
            body_text=serializer.validated_data.get('body_text', ''),
            body_html=serializer.validated_data.get('body_html', ''),
            cc_addresses=serializer.validated_data.get('cc_addresses'),
            bcc_addresses=serializer.validated_data.get('bcc_addresses')
        )
        
        if result['success']:
            email = result.get('email')
            return Response({
                'success': True,
                'message': 'Email sent successfully',
                'data': {
                    'id': email.id if email else None,
                    'message_id': result.get('message_id')
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'SEND_ERROR',
                    'message': result.get('error', 'Failed to send email')
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def draft(self, request):
        """Save draft"""
        serializer = EmailDraftSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid input data',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
        
        if not account:
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_ACCOUNT',
                    'message': 'No email account found'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Save draft
        email_service = EmailService(account)
        result = email_service.save_draft(
            to_addresses=serializer.validated_data.get('to_addresses', []),
            subject=serializer.validated_data.get('subject', ''),
            body_text=serializer.validated_data.get('body_text', ''),
            body_html=serializer.validated_data.get('body_html', '')
        )
        
        if result['success']:
            email = result.get('email')
            return Response({
                'success': True,
                'message': 'Draft saved',
                'data': {
                    'id': email.id if email else None
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'DRAFT_ERROR',
                    'message': result.get('error', 'Failed to save draft')
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark email as read/unread"""
        email = self.get_object()
        is_read = request.data.get('is_read', True)
        
        if is_read:
            email.mark_as_read()
            message = 'Email marked as read'
        else:
            email.mark_as_unread()
            message = 'Email marked as unread'
        
        return Response({
            'success': True,
            'message': message
        })
    
    @action(detail=True, methods=['patch'])
    def star(self, request, pk=None):
        """Star/unstar email"""
        email = self.get_object()
        is_starred = request.data.get('is_starred', True)
        
        email.is_starred = is_starred
        email.save(update_fields=['is_starred'])
        
        message = 'Email starred' if is_starred else 'Email unstarred'
        
        return Response({
            'success': True,
            'message': message
        })
    
    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        """Move email to folder"""
        email = self.get_object()
        folder = request.data.get('folder')
        
        if folder not in dict(Email.FOLDER_CHOICES):
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_FOLDER',
                    'message': 'Invalid folder name'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email.folder = folder
        email.save(update_fields=['folder'])
        
        return Response({
            'success': True,
            'message': f'Email moved to {folder}'
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete email"""
        email = self.get_object()
        permanent = request.query_params.get('permanent', 'false').lower() == 'true'
        
        if permanent:
            email.delete()
            message = 'Email permanently deleted'
        else:
            email.folder = 'trash'
            email.save(update_fields=['folder'])
            message = 'Email moved to trash'
        
        return Response({
            'success': True,
            'message': message
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search emails"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({
                'success': False,
                'error': {
                    'code': 'MISSING_QUERY',
                    'message': 'Search query is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
        
        if not account:
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_ACCOUNT',
                    'message': 'No email account found'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Search in subject, from_address, and body_text
        emails = Email.objects.filter(
            account=account
        ).filter(
            Q(subject__icontains=query) |
            Q(from_address__icontains=query) |
            Q(body_text__icontains=query)
        ).order_by('-received_at')
        
        # Apply filters
        folder = request.query_params.get('folder')
        if folder:
            emails = emails.filter(folder=folder)
        
        from_address = request.query_params.get('from')
        if from_address:
            emails = emails.filter(from_address__icontains=from_address)
        
        # Pagination
        page = self.paginate_queryset(emails)
        if page is not None:
            serializer = EmailListSerializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': self.paginator.get_paginated_response(serializer.data).data
            })
        
        serializer = EmailListSerializer(emails, many=True)
        return Response({
            'success': True,
            'data': {
                'count': emails.count(),
                'results': serializer.data
            }
        })


# Continue in next part...



# ============================================================================
# Contact Views
# ============================================================================

class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Contact operations"""
    serializer_class = ContactSerializer
    permission_classes = [IsEmailAccountOwner]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user).order_by('-is_favorite', 'name')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': self.paginator.get_paginated_response(serializer.data).data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'count': queryset.count(),
                'results': serializer.data
            }
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Contact deleted'
        }, status=status.HTTP_200_OK)


# ============================================================================
# Account Views
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def account_info_view(request):
    """Get account information"""
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    
    if not account:
        return Response({
            'success': False,
            'error': {
                'code': 'NO_ACCOUNT',
                'message': 'No email account found'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = EmailAccountSerializer(account)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def account_update_view(request):
    """Update account information"""
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    
    if not account:
        return Response({
            'success': False,
            'error': {
                'code': 'NO_ACCOUNT',
                'message': 'No email account found'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = EmailAccountSerializer(account, data=request.data, partial=True)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid input data',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# ============================================================================
# Statistics Views
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def email_stats_view(request):
    """Get email statistics"""
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    
    if not account:
        return Response({
            'success': False,
            'error': {
                'code': 'NO_ACCOUNT',
                'message': 'No email account found'
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    emails = Email.objects.filter(account=account)
    
    stats = {
        'total_emails': emails.count(),
        'unread_count': emails.filter(is_read=False).count(),
        'inbox_count': emails.filter(folder='inbox').count(),
        'sent_count': emails.filter(folder='sent').count(),
        'drafts_count': emails.filter(folder='drafts').count(),
        'trash_count': emails.filter(folder='trash').count(),
        'spam_count': emails.filter(folder='spam').count(),
        'starred_count': emails.filter(is_starred=True).count(),
        'storage_used_bytes': emails.aggregate(total=Sum('size_bytes'))['total'] or 0,
    }
    
    stats['storage_used_mb'] = round(stats['storage_used_bytes'] / (1024 * 1024), 2)
    
    serializer = EmailStatsSerializer(stats)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# ============================================================================
# Attachment Views
# ============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def attachment_download_view(request, attachment_id):
    """Download attachment"""
    try:
        attachment = EmailAttachment.objects.get(id=attachment_id)
        
        # Check if user owns the email
        if attachment.email.account.user != request.user:
            return Response({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'You do not have permission to access this attachment'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Return S3 URL or file content
        # For now, return the S3 URL
        return Response({
            'success': True,
            'data': {
                'download_url': attachment.s3_url,
                'filename': attachment.filename,
                'content_type': attachment.content_type,
                'size_bytes': attachment.size_bytes
            }
        })
        
    except EmailAttachment.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Attachment not found'
            }
        }, status=status.HTTP_404_NOT_FOUND)
