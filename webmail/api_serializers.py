from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmailAccount, Email, EmailAttachment, Contact

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class EmailAccountSerializer(serializers.ModelSerializer):
    """Serializer for EmailAccount model"""
    
    class Meta:
        model = EmailAccount
        fields = [
            'id', 'email_address', 'display_name', 'first_name', 'last_name',
            'mobile_number', 'alternate_email', 'signature', 'is_active',
            'ses_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ses_verified', 'created_at', 'updated_at']


class EmailAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for EmailAttachment model"""
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailAttachment
        fields = [
            'id', 'filename', 'content_type', 'size_bytes',
            'is_inline', 'download_url'
        ]
        read_only_fields = ['id']
    
    def get_download_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                f'/api/v1/webmail/attachments/{obj.id}/download/'
            )
        return None


class EmailListSerializer(serializers.ModelSerializer):
    """Serializer for Email list view (minimal data)"""
    body_preview = serializers.SerializerMethodField()
    has_attachments = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Email
        fields = [
            'id', 'from_address', 'from_name', 'to_addresses',
            'subject', 'body_preview', 'folder', 'is_read', 'is_starred',
            'is_important', 'has_attachments', 'attachment_count',
            'received_at', 'size_bytes'
        ]
        read_only_fields = ['id']
    
    def get_body_preview(self, obj):
        """Get first 150 characters of body text"""
        if obj.body_text:
            return obj.body_text[:150] + ('...' if len(obj.body_text) > 150 else '')
        return ''
    
    def get_has_attachments(self, obj):
        return obj.attachments.exists()
    
    def get_attachment_count(self, obj):
        return obj.attachments.count()


class EmailDetailSerializer(serializers.ModelSerializer):
    """Serializer for Email detail view (full data)"""
    attachments = EmailAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Email
        fields = [
            'id', 'message_id', 'from_address', 'from_name',
            'to_addresses', 'cc_addresses', 'bcc_addresses', 'reply_to',
            'subject', 'body_text', 'body_html', 'folder',
            'is_read', 'is_starred', 'is_important', 'is_draft',
            'sent_at', 'received_at', 'read_at', 'thread_id',
            'size_bytes', 'attachments'
        ]
        read_only_fields = ['id', 'message_id', 'sent_at', 'received_at', 'read_at']


class EmailSendSerializer(serializers.Serializer):
    """Serializer for sending emails"""
    to_addresses = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1
    )
    cc_addresses = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    bcc_addresses = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    subject = serializers.CharField(max_length=500)
    body_text = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if not data.get('body_text') and not data.get('body_html'):
            raise serializers.ValidationError(
                "Either body_text or body_html must be provided"
            )
        return data


class EmailDraftSerializer(serializers.Serializer):
    """Serializer for saving email drafts"""
    to_addresses = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    cc_addresses = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    subject = serializers.CharField(max_length=500, required=False, allow_blank=True)
    body_text = serializers.CharField(required=False, allow_blank=True)
    body_html = serializers.CharField(required=False, allow_blank=True)


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model"""
    
    class Meta:
        model = Contact
        fields = [
            'id', 'email', 'name', 'company', 'phone', 'notes',
            'is_favorite', 'email_count', 'last_emailed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email_count', 'last_emailed', 'created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    """Serializer for login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password"""
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for reset password"""
    email = serializers.EmailField()
    temporary_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data


class EmailStatsSerializer(serializers.Serializer):
    """Serializer for email statistics"""
    total_emails = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    inbox_count = serializers.IntegerField()
    sent_count = serializers.IntegerField()
    drafts_count = serializers.IntegerField()
    trash_count = serializers.IntegerField()
    spam_count = serializers.IntegerField()
    starred_count = serializers.IntegerField()
    storage_used_bytes = serializers.IntegerField()
    storage_used_mb = serializers.FloatField()
