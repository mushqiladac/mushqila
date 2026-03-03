import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class S3Service:
    """AWS S3 service for storing emails and attachments"""
    
    def __init__(self, aws_access_key=None, aws_secret_key=None, region='us-east-1', bucket_name=None):
        """Initialize S3 client"""
        self.aws_access_key = aws_access_key or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_key = aws_secret_key or settings.AWS_SECRET_ACCESS_KEY
        self.region = region or settings.AWS_REGION
        self.bucket_name = bucket_name or settings.AWS_S3_BUCKET_NAME
        
        self.client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
        
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
    
    def store_email(self, email_data, account_email, message_id):
        """
        Store email in S3
        
        Args:
            email_data: Dict containing email data
            account_email: Email account address
            message_id: Unique message ID
        
        Returns:
            dict: S3 key and URL
        """
        try:
            # Generate S3 key
            timestamp = datetime.now().strftime('%Y/%m/%d')
            s3_key = f"emails/{account_email}/inbox/{timestamp}/{message_id}.json"
            
            # Store email data as JSON
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(email_data, default=str),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            # Generate presigned URL (valid for 7 days)
            url = self.generate_presigned_url(s3_key, expiration=604800)
            
            logger.info(f"Email stored in S3: {s3_key}")
            return {
                'success': True,
                's3_key': s3_key,
                's3_url': url
            }
            
        except ClientError as e:
            logger.error(f"Failed to store email in S3: {e.response['Error']['Message']}")
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def store_attachment(self, file_content, filename, content_type, account_email, message_id):
        """
        Store email attachment in S3
        
        Args:
            file_content: File content (bytes)
            filename: Original filename
            content_type: MIME type
            account_email: Email account address
            message_id: Email message ID
        
        Returns:
            dict: S3 key and URL
        """
        try:
            # Generate S3 key
            timestamp = datetime.now().strftime('%Y/%m/%d')
            s3_key = f"emails/{account_email}/attachments/{timestamp}/{message_id}/{filename}"
            
            # Store attachment
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption='AES256',
                ContentDisposition=f'attachment; filename="{filename}"'
            )
            
            # Generate presigned URL (valid for 7 days)
            url = self.generate_presigned_url(s3_key, expiration=604800)
            
            logger.info(f"Attachment stored in S3: {s3_key}")
            return {
                'success': True,
                's3_key': s3_key,
                's3_url': url,
                'filename': filename
            }
            
        except ClientError as e:
            logger.error(f"Failed to store attachment in S3: {e.response['Error']['Message']}")
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def get_email(self, s3_key):
        """
        Retrieve email from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            dict: Email data
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            email_data = json.loads(response['Body'].read().decode('utf-8'))
            
            return {
                'success': True,
                'data': email_data
            }
            
        except ClientError as e:
            logger.error(f"Failed to retrieve email from S3: {e.response['Error']['Message']}")
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def get_attachment(self, s3_key):
        """
        Retrieve attachment from S3
        
        Args:
            s3_key: S3 object key
        
        Returns:
            dict: Attachment content and metadata
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'success': True,
                'content': response['Body'].read(),
                'content_type': response['ContentType'],
                'content_length': response['ContentLength']
            }
            
        except ClientError as e:
            logger.error(f"Failed to retrieve attachment from S3: {e.response['Error']['Message']}")
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def delete_email(self, s3_key):
        """Delete email from S3"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Email deleted from S3: {s3_key}")
            return {'success': True}
        except ClientError as e:
            logger.error(f"Failed to delete email from S3: {e.response['Error']['Message']}")
            return {'success': False, 'error': e.response['Error']['Message']}
    
    def delete_attachment(self, s3_key):
        """Delete attachment from S3"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Attachment deleted from S3: {s3_key}")
            return {'success': True}
        except ClientError as e:
            logger.error(f"Failed to delete attachment from S3: {e.response['Error']['Message']}")
            return {'success': False, 'error': e.response['Error']['Message']}
    
    def generate_presigned_url(self, s3_key, expiration=3600):
        """
        Generate presigned URL for S3 object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
        
        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e.response['Error']['Message']}")
            return None
    
    def list_emails(self, account_email, prefix='inbox/', max_keys=100):
        """
        List emails in S3 for an account
        
        Args:
            account_email: Email account address
            prefix: S3 prefix (folder)
            max_keys: Maximum number of keys to return
        
        Returns:
            list: List of S3 keys
        """
        try:
            full_prefix = f"emails/{account_email}/{prefix}"
            
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=full_prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                keys = [obj['Key'] for obj in response['Contents']]
                return {
                    'success': True,
                    'keys': keys,
                    'count': len(keys)
                }
            else:
                return {
                    'success': True,
                    'keys': [],
                    'count': 0
                }
                
        except ClientError as e:
            logger.error(f"Failed to list emails from S3: {e.response['Error']['Message']}")
            return {
                'success': False,
                'error': e.response['Error']['Message']
            }
    
    def create_bucket_if_not_exists(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
            return {'success': True, 'message': 'Bucket already exists'}
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    if self.region == 'us-east-1':
                        self.client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    logger.info(f"Bucket {self.bucket_name} created successfully")
                    return {'success': True, 'message': 'Bucket created'}
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error.response['Error']['Message']}")
                    return {'success': False, 'error': create_error.response['Error']['Message']}
            else:
                logger.error(f"Error checking bucket: {e.response['Error']['Message']}")
                return {'success': False, 'error': e.response['Error']['Message']}
