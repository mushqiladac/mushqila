import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class SESAutoConfigService:
    """Automatically configure SES for new email accounts"""
    
    def __init__(self):
        self.ses_client = boto3.client(
            'ses',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
        
        self.bucket_name = getattr(settings, 'AWS_S3_BUCKET_NAME', 'mushqila-emails')
    
    def verify_email_identity(self, email_address):
        """Verify email address in SES"""
        try:
            response = self.ses_client.verify_email_identity(
                EmailAddress=email_address
            )
            logger.info(f"Verification email sent to {email_address}")
            return {
                'success': True,
                'message': f'Verification email sent to {email_address}'
            }
        except ClientError as e:
            logger.error(f"Error verifying email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_verification_status(self, email_address):
        """Check if email is verified"""
        try:
            response = self.ses_client.get_identity_verification_attributes(
                Identities=[email_address]
            )
            
            attributes = response.get('VerificationAttributes', {})
            status = attributes.get(email_address, {}).get('VerificationStatus', 'NotStarted')
            
            return {
                'success': True,
                'verified': status == 'Success',
                'status': status
            }
        except ClientError as e:
            logger.error(f"Error checking verification: {e}")
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }
    
    def create_s3_inbox_structure(self, email_address):
        """Create S3 folder structure for email account"""
        folders = [
            f"{email_address}/inbox/",
            f"{email_address}/sent/",
            f"{email_address}/drafts/",
            f"{email_address}/trash/",
            f"{email_address}/attachments/"
        ]
        
        try:
            for folder in folders:
                # Create empty object to represent folder
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=folder,
                    Body=b''
                )
            
            logger.info(f"S3 inbox structure created for {email_address}")
            return {
                'success': True,
                'message': f'Inbox structure created for {email_address}',
                'bucket': self.bucket_name,
                'folders': folders
            }
        except ClientError as e:
            logger.error(f"Error creating S3 structure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def setup_new_email_account(self, email_address):
        """Complete setup for new email account"""
        results = {
            'email': email_address,
            'steps': []
        }
        
        # Step 1: Verify email in SES
        verify_result = self.verify_email_identity(email_address)
        results['steps'].append({
            'step': 'SES Verification',
            'success': verify_result['success'],
            'message': verify_result.get('message') or verify_result.get('error')
        })
        
        # Step 2: Create S3 inbox structure
        s3_result = self.create_s3_inbox_structure(email_address)
        results['steps'].append({
            'step': 'S3 Inbox Creation',
            'success': s3_result['success'],
            'message': s3_result.get('message') or s3_result.get('error')
        })
        
        if s3_result['success']:
            results['bucket'] = s3_result.get('bucket')
            results['inbox_prefix'] = f"{email_address}/inbox/"
        
        # Overall success
        results['success'] = all(step['success'] for step in results['steps'])
        
        return results
    
    def delete_email_account_resources(self, email_address):
        """Clean up SES and S3 resources for deleted account"""
        results = {
            'email': email_address,
            'steps': []
        }
        
        # Delete SES identity
        try:
            self.ses_client.delete_identity(Identity=email_address)
            results['steps'].append({
                'step': 'SES Identity Deletion',
                'success': True,
                'message': 'SES identity deleted'
            })
        except ClientError as e:
            results['steps'].append({
                'step': 'SES Identity Deletion',
                'success': False,
                'message': str(e)
            })
        except Exception as e:
            results['steps'].append({
                'step': 'SES Identity Deletion',
                'success': False,
                'message': str(e)
            })
        
        # Note: S3 folders are not deleted to preserve email history
        # Implement S3 deletion if needed
        
        results['success'] = all(step['success'] for step in results['steps'])
        return results
    
    def list_verified_emails(self):
        """List all verified email identities in SES"""
        try:
            response = self.ses_client.list_identities(
                IdentityType='EmailAddress'
            )
            return {
                'success': True,
                'identities': response.get('Identities', [])
            }
        except ClientError as e:
            logger.error(f"Error listing identities: {e}")
            return {
                'success': False,
                'error': str(e)
            }
