from django.utils import timezone
from django.db import transaction
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr, make_msgid
import logging

from ..models import Email, EmailAccount, EmailAttachment, Contact
from .ses_service import SESService
from .s3_service import S3Service

logger = logging.getLogger(__name__)


class EmailService:
    """Main email service combining SES and S3"""
    
    def __init__(self, email_account):
        """
        Initialize email service for an account
        
        Args:
            email_account: EmailAccount instance
        """
        self.account = email_account
        self.ses = SESService(
            aws_access_key=email_account.aws_access_key,
            aws_secret_key=email_account.aws_secret_key,
            region=email_account.aws_region
        )
        self.s3 = S3Service(
            aws_access_key=email_account.aws_access_key,
            aws_secret_key=email_account.aws_secret_key,
            bucket_name=email_account.s3_bucket_name
        )
    
    @transaction.atomic
    def send_email(self, to_addresses, subject, body_text, body_html=None,
                   cc_addresses=None, bcc_addresses=None, reply_to=None,
                   attachments=None, save_to_sent=True):
        """
        Send email and save to database
        
        Args:
            to_addresses: List of recipient emails
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            cc_addresses: List of CC emails (optional)
            bcc_addresses: List of BCC emails (optional)
            reply_to: Reply-to address (optional)
            attachments: List of file objects (optional)
            save_to_sent: Save to sent folder (default True)
        
        Returns:
            dict: Result with email object
        """
        try:
            # Generate message ID
            message_id = make_msgid(domain=self.account.email_address.split('@')[1])
            
            # Prepare email data
            email_data = {
                'message_id': message_id,
                'from_address': self.account.email_address,
                'from_name': self.account.display_name,
                'to_addresses': to_addresses if isinstance(to_addresses, list) else [to_addresses],
                'cc_addresses': cc_addresses or [],
                'bcc_addresses': bcc_addresses or [],
                'subject': subject,
                'body_text': body_text,
                'body_html': body_html or '',
                'sent_at': timezone.now().isoformat()
            }
            
            # Send via SES
            if attachments:
                # Send with attachments using raw email
                result = self._send_with_attachments(
                    email_data, attachments, reply_to
                )
            else:
                # Send simple email
                from_email = formataddr((self.account.display_name, self.account.email_address))
                result = self.ses.send_email(
                    from_email=from_email,
                    to_emails=email_data['to_addresses'],
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html,
                    cc_emails=cc_addresses,
                    bcc_emails=bcc_addresses,
                    reply_to=reply_to
                )
            
            if not result['success']:
                return result
            
            # Store email in S3
            s3_result = self.s3.store_email(
                email_data=email_data,
                account_email=self.account.email_address,
                message_id=message_id
            )
            
            if not s3_result['success']:
                logger.warning(f"Failed to store email in S3: {s3_result.get('error')}")
            
            # Save to database
            if save_to_sent:
                email = Email.objects.create(
                    account=self.account,
                    message_id=message_id,
                    from_address=self.account.email_address,
                    from_name=self.account.display_name,
                    to_addresses=email_data['to_addresses'],
                    cc_addresses=email_data['cc_addresses'],
                    bcc_addresses=email_data['bcc_addresses'],
                    reply_to=reply_to or '',
                    subject=subject,
                    body_text=body_text,
                    body_html=body_html or '',
                    folder='sent',
                    is_read=True,
                    sent_at=timezone.now(),
                    s3_key=s3_result.get('s3_key', ''),
                    s3_url=s3_result.get('s3_url', ''),
                    size_bytes=len(body_text) + len(body_html or '')
                )
                
                # Save attachments
                if attachments:
                    self._save_attachments(email, attachments, message_id)
                
                # Update contacts
                self._update_contacts(email_data['to_addresses'])
            
            return {
                'success': True,
                'message_id': result['message_id'],
                'email': email if save_to_sent else None
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_with_attachments(self, email_data, attachments, reply_to=None):
        """Send email with attachments using raw MIME message"""
        try:
            # Create MIME message
            msg = MIMEMultipart()
            msg['From'] = formataddr((email_data['from_name'], email_data['from_address']))
            msg['To'] = ', '.join(email_data['to_addresses'])
            msg['Subject'] = email_data['subject']
            msg['Message-ID'] = email_data['message_id']
            
            if email_data['cc_addresses']:
                msg['Cc'] = ', '.join(email_data['cc_addresses'])
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add body
            if email_data['body_html']:
                msg.attach(MIMEText(email_data['body_text'], 'plain'))
                msg.attach(MIMEText(email_data['body_html'], 'html'))
            else:
                msg.attach(MIMEText(email_data['body_text'], 'plain'))
            
            # Add attachments
            for attachment in attachments:
                part = MIMEApplication(attachment.read())
                part.add_header('Content-Disposition', 'attachment', filename=attachment.name)
                msg.attach(part)
                attachment.seek(0)  # Reset file pointer
            
            # Send raw email
            all_recipients = email_data['to_addresses'] + email_data['cc_addresses'] + email_data['bcc_addresses']
            return self.ses.send_raw_email(
                raw_message=msg.as_string(),
                from_email=email_data['from_address'],
                to_emails=all_recipients
            )
            
        except Exception as e:
            logger.error(f"Failed to send email with attachments: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_attachments(self, email, attachments, message_id):
        """Save attachments to S3 and database"""
        for attachment in attachments:
            try:
                # Store in S3
                s3_result = self.s3.store_attachment(
                    file_content=attachment.read(),
                    filename=attachment.name,
                    content_type=attachment.content_type,
                    account_email=self.account.email_address,
                    message_id=message_id
                )
                
                if s3_result['success']:
                    # Save to database
                    EmailAttachment.objects.create(
                        email=email,
                        filename=attachment.name,
                        content_type=attachment.content_type,
                        size_bytes=attachment.size,
                        s3_key=s3_result['s3_key'],
                        s3_url=s3_result['s3_url']
                    )
                
                attachment.seek(0)  # Reset file pointer
                
            except Exception as e:
                logger.error(f"Failed to save attachment {attachment.name}: {str(e)}")
    
    def _update_contacts(self, email_addresses):
        """Update or create contacts"""
        for email_address in email_addresses:
            try:
                contact, created = Contact.objects.get_or_create(
                    user=self.account.user,
                    email=email_address,
                    defaults={'email_count': 0}
                )
                contact.email_count += 1
                contact.last_emailed = timezone.now()
                contact.save(update_fields=['email_count', 'last_emailed'])
            except Exception as e:
                logger.error(f"Failed to update contact {email_address}: {str(e)}")
    
    @transaction.atomic
    def receive_email(self, raw_email_data):
        """
        Process received email and store in inbox
        
        Args:
            raw_email_data: Raw email data from SES
        
        Returns:
            Email: Created email object
        """
        try:
            # Parse email data
            message_id = raw_email_data.get('messageId', make_msgid())
            
            email_data = {
                'message_id': message_id,
                'from_address': raw_email_data.get('from', ''),
                'to_addresses': raw_email_data.get('to', []),
                'cc_addresses': raw_email_data.get('cc', []),
                'subject': raw_email_data.get('subject', ''),
                'body_text': raw_email_data.get('text', ''),
                'body_html': raw_email_data.get('html', ''),
                'received_at': timezone.now().isoformat()
            }
            
            # Store in S3
            s3_result = self.s3.store_email(
                email_data=email_data,
                account_email=self.account.email_address,
                message_id=message_id
            )
            
            # Save to database
            email = Email.objects.create(
                account=self.account,
                message_id=message_id,
                from_address=email_data['from_address'],
                to_addresses=email_data['to_addresses'],
                cc_addresses=email_data['cc_addresses'],
                subject=email_data['subject'],
                body_text=email_data['body_text'],
                body_html=email_data['body_html'],
                folder='inbox',
                is_read=False,
                received_at=timezone.now(),
                s3_key=s3_result.get('s3_key', ''),
                s3_url=s3_result.get('s3_url', ''),
                size_bytes=len(email_data['body_text']) + len(email_data['body_html'])
            )
            
            logger.info(f"Email received and stored: {message_id}")
            return email
            
        except Exception as e:
            logger.error(f"Failed to receive email: {str(e)}")
            raise
    
    def save_draft(self, to_addresses, subject, body_text, body_html=None):
        """Save email as draft"""
        try:
            message_id = make_msgid(domain=self.account.email_address.split('@')[1])
            
            email = Email.objects.create(
                account=self.account,
                message_id=message_id,
                from_address=self.account.email_address,
                from_name=self.account.display_name,
                to_addresses=to_addresses if isinstance(to_addresses, list) else [to_addresses],
                subject=subject,
                body_text=body_text,
                body_html=body_html or '',
                folder='drafts',
                is_draft=True,
                is_read=True
            )
            
            return {
                'success': True,
                'email': email
            }
        except Exception as e:
            logger.error(f"Failed to save draft: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def move_to_folder(self, email, folder):
        """Move email to different folder"""
        try:
            email.folder = folder
            email.save(update_fields=['folder'])
            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to move email: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_email(self, email, permanent=False):
        """Delete email (move to trash or permanent delete)"""
        try:
            if permanent:
                # Delete from S3
                if email.s3_key:
                    self.s3.delete_email(email.s3_key)
                
                # Delete attachments from S3
                for attachment in email.attachments.all():
                    if attachment.s3_key:
                        self.s3.delete_attachment(attachment.s3_key)
                
                # Delete from database
                email.delete()
            else:
                # Move to trash
                email.folder = 'trash'
                email.save(update_fields=['folder'])
            
            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to delete email: {str(e)}")
            return {'success': False, 'error': str(e)}
