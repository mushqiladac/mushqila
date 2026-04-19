from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import uuid
import secrets
import string
from datetime import timedelta

User = get_user_model()


class EmailAccount(models.Model):
    """User's email account configuration"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_accounts')
    email_address = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255)
    
    # User Information
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=255, default='')  # Hashed password for webmail login
    mobile_number = models.CharField(max_length=20, blank=True)
    alternate_email = models.EmailField(blank=True)
    
    # Password Reset
    reset_token = models.CharField(max_length=100, blank=True)
    reset_token_created = models.DateTimeField(null=True, blank=True)
    
    # AWS SES Configuration
    aws_access_key = models.CharField(max_length=255, blank=True)
    aws_secret_key = models.CharField(max_length=255, blank=True)
    aws_region = models.CharField(max_length=50, default='us-east-1')
    ses_verified = models.BooleanField(default=False)
    
    # S3 Configuration for storing emails
    s3_bucket_name = models.CharField(max_length=255, blank=True)
    s3_inbox_prefix = models.CharField(max_length=255, default='inbox/')
    
    # Settings
    signature = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        
    def __str__(self):
        return f"{self.display_name} <{self.email_address}>"
    
    def set_password(self, raw_password):
        """Set hashed password for webmail login"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if provided password matches"""
        return check_password(raw_password, self.password)
    
    def generate_reset_token(self):
        """Generate a temporary password reset token"""
        # Generate random 8-character token
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(8))
        
        self.reset_token = token
        self.reset_token_created = timezone.now()
        self.save(update_fields=['reset_token', 'reset_token_created'])
        
        return token
    
    def is_reset_token_valid(self, token):
        """Check if reset token is valid (matches and not expired)"""
        if not self.reset_token or not self.reset_token_created:
            return False
        
        # Check if token matches
        if self.reset_token != token:
            return False
        
        # Check if token is expired (15 minutes)
        expiry_time = self.reset_token_created + timedelta(minutes=15)
        if timezone.now() > expiry_time:
            return False
        
        return True
    
    def clear_reset_token(self):
        """Clear reset token after use"""
        self.reset_token = ''
        self.reset_token_created = None
        self.save(update_fields=['reset_token', 'reset_token_created'])


class Email(models.Model):
    """Email message stored in database with S3 reference"""
    
    FOLDER_CHOICES = [
        ('inbox', 'Inbox'),
        ('sent', 'Sent'),
        ('drafts', 'Drafts'),
        ('trash', 'Trash'),
        ('spam', 'Spam'),
        ('archive', 'Archive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='emails')
    
    # Email Headers
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    from_address = models.EmailField(db_index=True)
    from_name = models.CharField(max_length=255, blank=True)
    to_addresses = models.JSONField(default=list)  # List of email addresses
    cc_addresses = models.JSONField(default=list, blank=True)
    bcc_addresses = models.JSONField(default=list, blank=True)
    reply_to = models.EmailField(blank=True)
    
    # Email Content
    subject = models.CharField(max_length=500, db_index=True)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    
    # S3 Storage
    s3_key = models.CharField(max_length=500, blank=True)  # S3 object key
    s3_url = models.URLField(max_length=1000, blank=True)
    
    # Metadata
    folder = models.CharField(max_length=20, choices=FOLDER_CHOICES, default='inbox', db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    is_starred = models.BooleanField(default=False, db_index=True)
    is_important = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(default=timezone.now, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Thread
    thread_id = models.CharField(max_length=255, blank=True, db_index=True)
    in_reply_to = models.CharField(max_length=255, blank=True)
    references = models.TextField(blank=True)
    
    # Size
    size_bytes = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['account', 'folder', '-received_at']),
            models.Index(fields=['account', 'is_read', '-received_at']),
            models.Index(fields=['thread_id', '-received_at']),
        ]
        
    def __str__(self):
        return f"{self.subject} - {self.from_address}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])


class EmailAttachment(models.Model):
    """Email attachments stored in S3"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='attachments')
    
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size_bytes = models.IntegerField()
    
    # S3 Storage
    s3_key = models.CharField(max_length=500)
    s3_url = models.URLField(max_length=1000)
    
    # Inline attachment (for images in HTML)
    content_id = models.CharField(max_length=255, blank=True)
    is_inline = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['filename']
        
    def __str__(self):
        return f"{self.filename} ({self.size_bytes} bytes)"


class EmailLabel(models.Model):
    """Custom labels/tags for emails"""
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#3b82f6')  # Hex color
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['account', 'name']
        ordering = ['name']
        
    def __str__(self):
        return self.name


class EmailLabelAssignment(models.Model):
    """Many-to-many relationship between emails and labels"""
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='label_assignments')
    label = models.ForeignKey(EmailLabel, on_delete=models.CASCADE, related_name='email_assignments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['email', 'label']


class EmailFilter(models.Model):
    """Email filtering rules"""
    
    CONDITION_CHOICES = [
        ('from', 'From'),
        ('to', 'To'),
        ('subject', 'Subject'),
        ('body', 'Body'),
    ]
    
    ACTION_CHOICES = [
        ('move_to_folder', 'Move to Folder'),
        ('add_label', 'Add Label'),
        ('mark_as_read', 'Mark as Read'),
        ('mark_as_starred', 'Mark as Starred'),
        ('delete', 'Delete'),
    ]
    
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='filters')
    name = models.CharField(max_length=255)
    
    # Condition
    condition_field = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    condition_value = models.CharField(max_length=255)
    condition_operator = models.CharField(max_length=20, default='contains')  # contains, equals, starts_with
    
    # Action
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    action_value = models.CharField(max_length=255, blank=True)  # folder name or label name
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name


class EmailTemplate(models.Model):
    """Reusable email templates"""
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=500)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class Contact(models.Model):
    """Email contacts/address book"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    
    email = models.EmailField(db_index=True)
    name = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    
    # Frequency tracking
    email_count = models.IntegerField(default=0)
    last_emailed = models.DateTimeField(null=True, blank=True)
    
    is_favorite = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'email']
        ordering = ['-is_favorite', 'name', 'email']
        
    def __str__(self):
        return f"{self.name} <{self.email}>" if self.name else self.email
