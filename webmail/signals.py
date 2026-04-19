from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import EmailAccount
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EmailAccount)
def auto_configure_email_account(sender, instance, created, **kwargs):
    """Automatically configure SES and S3 when new email account is created"""
    if created:
        logger.info(f"New email account created: {instance.email_address}")
        
        try:
            from .services.ses_auto_config import SESAutoConfigService
            
            # Initialize auto-config service
            config_service = SESAutoConfigService()
            
            # Setup email account
            result = config_service.setup_new_email_account(instance.email_address)
            
            if result['success']:
                logger.info(f"Auto-configuration successful for {instance.email_address}")
                
                # Update account with S3 configuration
                if result.get('bucket'):
                    instance.s3_bucket_name = result['bucket']
                if result.get('inbox_prefix'):
                    instance.s3_inbox_prefix = result['inbox_prefix']
                
                instance.save(update_fields=['s3_bucket_name', 's3_inbox_prefix'])
                
                logger.info(f"Updated S3 configuration for {instance.email_address}")
            else:
                logger.error(f"Auto-configuration failed for {instance.email_address}: {result}")
        
        except ImportError as e:
            logger.warning(f"SES auto-config not available: {e}")
        except Exception as e:
            logger.error(f"Error in auto-configuration: {e}")


@receiver(post_delete, sender=EmailAccount)
def cleanup_email_account_resources(sender, instance, **kwargs):
    """Clean up AWS resources when email account is deleted"""
    logger.info(f"Email account deleted: {instance.email_address}")
    
    try:
        from .services.ses_auto_config import SESAutoConfigService
        
        # Initialize auto-config service
        config_service = SESAutoConfigService()
        
        # Cleanup resources
        result = config_service.delete_email_account_resources(instance.email_address)
        
        if result['success']:
            logger.info(f"Resource cleanup successful for {instance.email_address}")
        else:
            logger.error(f"Resource cleanup failed for {instance.email_address}: {result}")
    
    except ImportError as e:
        logger.warning(f"SES auto-config not available: {e}")
    except Exception as e:
        logger.error(f"Error in resource cleanup: {e}")
