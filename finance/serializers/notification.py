from rest_framework import serializers
from ..models import FinanceNotification
from ..models.notification import NotificationTemplate


class FinanceNotificationSerializer(serializers.ModelSerializer):
    """Serializer for FinanceNotification model"""
    
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = FinanceNotification
        fields = [
            'id', 'user', 'notification_type', 'notification_type_display',
            'title', 'title_ar', 'message', 'message_ar', 'is_read',
            'is_push_sent', 'action_url', 'action_text', 'action_text_ar',
            'ticket_sale', 'submission', 'metadata', 'created_at', 'read_at'
        ]
        read_only_fields = [
            'id', 'user', 'is_push_sent', 'ticket_sale', 'submission',
            'created_at', 'read_at'
        ]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model"""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'template_type', 'subject', 'subject_ar',
            'html_content', 'html_content_ar', 'text_content',
            'text_content_ar', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = FinanceNotification
        fields = [
            'notification_type', 'title', 'title_ar', 'message',
            'message_ar', 'action_url', 'action_text', 'action_text_ar',
            'ticket_sale', 'submission', 'metadata'
        ]
    
    def validate(self, attrs):
        """Validate notification data"""
        title = attrs.get('title', '')
        title_ar = attrs.get('title_ar', '')
        message = attrs.get('message', '')
        message_ar = attrs.get('message_ar', '')
        
        if not title and not title_ar:
            raise serializers.ValidationError("Title (English or Arabic) is required")
        
        if not message and not message_ar:
            raise serializers.ValidationError("Message (English or Arabic) is required")
        
        return attrs


class BulkNotificationSerializer(serializers.Serializer):
    """Serializer for bulk notification creation"""
    
    user_ids = serializers.ListField(child=serializers.IntegerField())
    notification_type = serializers.CharField(max_length=20)
    title = serializers.CharField(max_length=255)
    title_ar = serializers.CharField(max_length=255, required=False, allow_blank=True)
    message = serializers.CharField()
    message_ar = serializers.CharField(required=False, allow_blank=True)
    action_url = serializers.URLField(required=False, allow_blank=True)
    action_text = serializers.CharField(max_length=50, required=False, allow_blank=True)
    action_text_ar = serializers.CharField(max_length=50, required=False, allow_blank=True)
    metadata = serializers.JSONField(default=dict)
    
    def validate_user_ids(self, value):
        """Validate user IDs"""
        if not value:
            raise serializers.ValidationError("At least one user ID is required")
        return value
    
    def validate(self, attrs):
        """Validate bulk notification data"""
        title = attrs.get('title', '')
        title_ar = attrs.get('title_ar', '')
        message = attrs.get('message', '')
        message_ar = attrs.get('message_ar', '')
        
        if not title and not title_ar:
            raise serializers.ValidationError("Title (English or Arabic) is required")
        
        if not message and not message_ar:
            raise serializers.ValidationError("Message (English or Arabic) is required")
        
        return attrs


class EmailNotificationSerializer(serializers.Serializer):
    """Serializer for sending email notifications"""
    
    template_type = serializers.CharField(max_length=50)
    recipient_email = serializers.EmailField()
    context = serializers.JSONField(default=dict)
    language = serializers.CharField(max_length=2, default='en')
    
    def validate_template_type(self, value):
        """Validate template type exists"""
        if not NotificationTemplate.objects.filter(template_type=value, is_active=True).exists():
            raise serializers.ValidationError("Template type not found or inactive")
        return value
    
    def validate_language(self, value):
        """Validate language"""
        if value not in ['en', 'ar']:
            raise serializers.ValidationError("Language must be 'en' or 'ar'")
        return value
