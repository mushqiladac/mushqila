# accounts/signals.py (COMPLETELY FIXED VERSION)

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
import logging

from .models import User, UserProfile, Document, Notification

logger = logging.getLogger(__name__)


# ==================== User Signals ====================

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile whenever a new User is created.
    """
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"Created UserProfile for user {instance.email}")
        except Exception as e:
            logger.error(f"Error creating UserProfile for user {instance.email}: {str(e)}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save UserProfile whenever User is saved.
    """
    try:
        instance.profile.save()
    except:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)


@receiver(pre_save, sender=User)
def user_pre_save_handler(sender, instance, **kwargs):
    """
    Handle pre-save operations for User model.
    """
    # Ensure username is set to email
    if not instance.username:
        instance.username = instance.email
    
    # Generate referral code for agents
    if not instance.referral_code and instance.user_type in ['agent', 'super_agent', 'sub_agent']:
        import random
        import string
        while True:
            code = 'SA' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not User.objects.filter(referral_code=code).exists():
                instance.referral_code = code
                break


@receiver(post_save, sender=User)
def user_status_changed_handler(sender, instance, created, **kwargs):
    """
    Handle user status changes and send notifications.
    """
    if not created:
        try:
            # Get original status from database
            try:
                original_user = User.objects.get(id=instance.id)
                original_status = original_user.status
            except User.DoesNotExist:
                original_status = None
            
            # Check if status changed
            if original_status and original_status != instance.status:
                # Create notification for user
                Notification.objects.create(
                    user=instance,
                    notification_type='system',
                    title='Account Status Updated',
                    message=f'Your account status has been changed from {original_status} to {instance.status}.',
                    action_url='/accounts/profile/'
                )
                
                logger.info(f"User {instance.email} status changed from {original_status} to {instance.status}")
        
        except Exception as e:
            logger.error(f"Error in user_status_changed_handler for {instance.email}: {str(e)}")


# ==================== Document Signals ====================

@receiver(post_save, sender=Document)
def document_status_changed_handler(sender, instance, created, **kwargs):
    """
    Handle document status changes and update user KYC status.
    """
    if not created:
        try:
            original_status = None
            try:
                original_doc = Document.objects.get(id=instance.id)
                original_status = original_doc.status
            except Document.DoesNotExist:
                pass
            
            # Check if status changed to verified
            if original_status != 'verified' and instance.status == 'verified':
                user = instance.user
                
                # Count verified documents for the user
                verified_docs = Document.objects.filter(
                    user=user,
                    status='verified'
                ).count()
                
                # Update user KYC status based on verified documents
                required_docs = 2  # Minimum required documents for KYC
                if verified_docs >= required_docs:
                    if not user.kyc_verified:
                        user.kyc_verified = True
                        user.kyc_submitted = timezone.now()
                        user.save(update_fields=['kyc_verified', 'kyc_submitted'])
                        
                        # Create notification
                        Notification.objects.create(
                            user=user,
                            notification_type='success',
                            title='KYC Verified',
                            message='Your KYC has been successfully verified.',
                            action_url='/accounts/profile/'
                        )
                
                # Create notification for document verification
                Notification.objects.create(
                    user=user,
                    notification_type='success',
                    title='Document Verified',
                    message=f'Your {instance.get_document_type_display()} has been verified.',
                    action_url='/accounts/kyc/'
                )
            
            # Check if status changed to rejected
            elif original_status != 'rejected' and instance.status == 'rejected':
                Notification.objects.create(
                    user=instance.user,
                    notification_type='error',
                    title='Document Rejected',
                    message=f'Your {instance.get_document_type_display()} has been rejected. {instance.verification_notes}',
                    action_url='/accounts/kyc/'
                )
        
        except Exception as e:
            logger.error(f"Error in document_status_changed_handler: {str(e)}")


@receiver(pre_save, sender=Document)
def document_expiry_check(sender, instance, **kwargs):
    """
    Check document expiry before saving.
    """
    if instance.expiry_date and instance.expiry_date < timezone.now().date():
        if instance.status == 'verified':
            instance.status = 'expired'
            
            # Create notification
            Notification.objects.create(
                user=instance.user,
                notification_type='warning',
                title='Document Expired',
                message=f'Your {instance.get_document_type_display()} has expired. Please upload a new document.',
                action_url='/accounts/kyc/'
            )


# ==================== Notification Signals ====================

@receiver(post_save, sender=Notification)
def notification_created_handler(sender, instance, created, **kwargs):
    """
    Handle new notification creation.
    """
    if created:
        try:
            logger.info(f"Created notification for user {instance.user.email}: {instance.title}")
        except Exception as e:
            logger.error(f"Error in notification_created_handler: {str(e)}")


# ==================== Custom Signal for Saudi Phone Validation ====================

@receiver(pre_save, sender=User)
def validate_saudi_phone(sender, instance, **kwargs):
    """
    Validate Saudi phone numbers before saving.
    """
    if instance.phone:
        # Format Saudi phone numbers
        phone = instance.phone.strip()
        
        # Remove any non-digit characters except +
        import re
        if phone.startswith('+9665'):
            # Already in correct format
            pass
        elif phone.startswith('9665'):
            instance.phone = '+' + phone
        elif phone.startswith('05'):
            instance.phone = '+966' + phone[1:]
        elif phone.startswith('5') and len(phone) == 9:
            instance.phone = '+966' + phone
        
        # Log formatting
        logger.debug(f"Formatted phone for {instance.email}: {phone} -> {instance.phone}")


# ==================== Initialize Signals ====================

def ready():
    """
    Function to ensure signals are connected.
    """
    logger.info("Accounts signals initialized")