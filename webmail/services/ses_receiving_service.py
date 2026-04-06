import boto3
import email
from email import policy
from datetime import datetime
from django.conf import settings
from webmail.models import Email, EmailAccount
import logging

logger = logging.getLogger(__name__)


class SESReceivingService:
    """Service to fetch incoming emails from AWS SES via S3"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=getattr(settings, 'AWS_SES_RECEIVING_REGION', 'us-east-1'),
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket = getattr(settings, 'AWS_S3_INCOMING_BUCKET', 'mushqila-incoming-emails')
    
    def fetch_new_emails(self):
        """Fetch new emails from S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix='incoming/'
            )
            
            if 'Contents' not in response:
                logger.info("No new emails found")
                return []
            
            new_emails = []
            for obj in response['Contents']:
                email_key = obj['Key']
                
                try:
                    # Download email from S3
                    email_obj = self.s3_client.get_object(
                        Bucket=self.bucket,
                        Key=email_key
                    )
                    
                    # Parse email
                    raw_email = email_obj['Body'].read()
                    msg = email.message_from_bytes(raw_email, policy=policy.default)
                    
                    # Extract email details
                    email_data = {
                        'message_id': msg.get('Message-ID', ''),
                        'from_address': msg.get('From', ''),
                        'to_addresses': msg.get('To', ''),
                        'cc_addresses': msg.get('Cc', ''),
                        'subject': msg.get('Subject', '(No Subject)'),
                        'date': msg.get('Date', ''),
                        'body_text': self._get_body(msg, 'plain'),
                        'body_html': self._get_body(msg, 'html'),
                    }
                    
                    # Save to database
                    saved_email = self._save_email(email_data)
                    if saved_email:
                        new_emails.append(email_data)
                        logger.info(f"Saved email: {email_data['subject']}")
                    
                    # Delete from S3 after successful processing
                    self.s3_client.delete_object(
                        Bucket=self.bucket,
                        Key=email_key
                    )
                    logger.info(f"Deleted processed email from S3: {email_key}")
                    
                except Exception as e:
                    logger.error(f"Error processing email {email_key}: {str(e)}")
                    continue
            
            return new_emails
            
        except Exception as e:
            logger.error(f"Error fetching emails from S3: {str(e)}")
            return []
    
    def _get_body(self, msg, content_type):
        """Extract email body (text or html)"""
        try:
            for part in msg.walk():
                if part.get_content_type() == f'text/{content_type}':
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode('utf-8', errors='ignore')
            return ''
        except Exception as e:
            logger.error(f"Error extracting {content_type} body: {str(e)}")
            return ''
    
    def _save_email(self, email_data):
        """Save email to database"""
        try:
            # Extract recipient email address
            to_address = email_data['to_addresses'].split(',')[0].strip()
            # Remove name part if exists (e.g., "Name <email@domain.com>" -> "email@domain.com")
            if '<' in to_address:
                to_address = to_address.split('<')[1].split('>')[0].strip()
            
            # Find recipient's account
            account = EmailAccount.objects.filter(
                email_address__iexact=to_address
            ).first()
            
            if not account:
                # Try to find by domain
                domain = to_address.split('@')[1] if '@' in to_address else None
                if domain:
                    account = EmailAccount.objects.filter(
                        email_address__icontains=f'@{domain}'
                    ).first()
            
            if not account:
                logger.warning(f"No account found for {to_address}")
                return None
            
            # Check if email already exists
            if Email.objects.filter(
                account=account,
                message_id=email_data['message_id']
            ).exists():
                logger.info(f"Email already exists: {email_data['message_id']}")
                return None
            
            # Create email
            email_obj = Email.objects.create(
                account=account,
                message_id=email_data['message_id'],
                from_address=email_data['from_address'],
                to_addresses=email_data['to_addresses'],
                cc_addresses=email_data.get('cc_addresses', ''),
                subject=email_data['subject'],
                body_text=email_data['body_text'],
                body_html=email_data['body_html'],
                folder='inbox',
                is_read=False,
                received_at=datetime.now()
            )
            
            return email_obj
            
        except Exception as e:
            logger.error(f"Error saving email to database: {str(e)}")
            return None
