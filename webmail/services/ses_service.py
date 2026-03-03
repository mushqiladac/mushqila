import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SESService:
    """AWS SES service for sending emails"""
    
    def __init__(self, aws_access_key=None, aws_secret_key=None, region='us-east-1'):
        """Initialize SES client"""
        self.aws_access_key = aws_access_key or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_key = aws_secret_key or settings.AWS_SECRET_ACCESS_KEY
        self.region = region or settings.AWS_REGION
        
        self.client = boto3.client(
            'ses',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
    
    def send_email(self, from_email, to_emails, subject, body_text, body_html=None, 
                   cc_emails=None, bcc_emails=None, reply_to=None, attachments=None):
        """
        Send email via AWS SES
        
        Args:
            from_email: Sender email address
            to_emails: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            cc_emails: List of CC email addresses (optional)
            bcc_emails: List of BCC email addresses (optional)
            reply_to: Reply-to email address (optional)
            attachments: List of attachment dicts (optional)
        
        Returns:
            dict: Response from SES with MessageId
        """
        try:
            # Prepare destination
            destination = {'ToAddresses': to_emails if isinstance(to_emails, list) else [to_emails]}
            
            if cc_emails:
                destination['CcAddresses'] = cc_emails if isinstance(cc_emails, list) else [cc_emails]
            
            if bcc_emails:
                destination['BccAddresses'] = bcc_emails if isinstance(bcc_emails, list) else [bcc_emails]
            
            # Prepare message
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {}
            }
            
            if body_text:
                message['Body']['Text'] = {'Data': body_text, 'Charset': 'UTF-8'}
            
            if body_html:
                message['Body']['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}
            
            # Send email
            kwargs = {
                'Source': from_email,
                'Destination': destination,
                'Message': message
            }
            
            if reply_to:
                kwargs['ReplyToAddresses'] = [reply_to] if isinstance(reply_to, str) else reply_to
            
            response = self.client.send_email(**kwargs)
            
            logger.info(f"Email sent successfully. MessageId: {response['MessageId']}")
            return {
                'success': True,
                'message_id': response['MessageId'],
                'response': response
            }
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send email: {error_message}")
            return {
                'success': False,
                'error': error_message,
                'error_code': e.response['Error']['Code']
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_raw_email(self, raw_message, from_email, to_emails):
        """
        Send raw email (with attachments) via AWS SES
        
        Args:
            raw_message: Raw MIME message
            from_email: Sender email address
            to_emails: List of recipient email addresses
        
        Returns:
            dict: Response from SES
        """
        try:
            response = self.client.send_raw_email(
                Source=from_email,
                Destinations=to_emails if isinstance(to_emails, list) else [to_emails],
                RawMessage={'Data': raw_message}
            )
            
            logger.info(f"Raw email sent successfully. MessageId: {response['MessageId']}")
            return {
                'success': True,
                'message_id': response['MessageId'],
                'response': response
            }
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send raw email: {error_message}")
            return {
                'success': False,
                'error': error_message
            }
    
    def verify_email_identity(self, email_address):
        """
        Verify an email address with AWS SES
        
        Args:
            email_address: Email address to verify
        
        Returns:
            dict: Verification status
        """
        try:
            response = self.client.verify_email_identity(EmailAddress=email_address)
            logger.info(f"Verification email sent to {email_address}")
            return {
                'success': True,
                'message': f'Verification email sent to {email_address}',
                'response': response
            }
        except ClientError as e:
            logger.error(f"Failed to verify email: {e.response['Error']['Message']}")
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def get_send_quota(self):
        """Get SES sending quota"""
        try:
            response = self.client.get_send_quota()
            return {
                'success': True,
                'max_24_hour_send': response['Max24HourSend'],
                'max_send_rate': response['MaxSendRate'],
                'sent_last_24_hours': response['SentLast24Hours']
            }
        except ClientError as e:
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def get_send_statistics(self):
        """Get SES sending statistics"""
        try:
            response = self.client.get_send_statistics()
            return {
                'success': True,
                'data_points': response['SendDataPoints']
            }
        except ClientError as e:
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def list_verified_email_addresses(self):
        """List all verified email addresses"""
        try:
            response = self.client.list_verified_email_addresses()
            return {
                'success': True,
                'verified_emails': response['VerifiedEmailAddresses']
            }
        except ClientError as e:
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
