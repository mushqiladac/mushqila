from django.db import models
from django.utils.translation import gettext_lazy as _


class FinanceNotification(models.Model):
    """Notification system for finance app"""
    
    class NotificationType(models.TextChoices):
        INFO = 'info', _('Information')
        SUCCESS = 'success', _('Success')
        WARNING = 'warning', _('Warning')
        ERROR = 'error', _('Error')
        SUBMISSION = 'submission', _('Submission')
        APPROVAL = 'approval', _('Approval')
        REJECTION = 'rejection', _('Rejection')
        PAYMENT = 'payment', _('Payment')
        DUE = 'due', _('Payment Due')
    
    user = models.ForeignKey('FinanceUser', on_delete=models.CASCADE, related_name='finance_notifications')
    
    notification_type = models.CharField(_('notification type'), max_length=20, choices=NotificationType.choices, default=NotificationType.INFO)
    
    title = models.CharField(_('title'), max_length=255)
    title_ar = models.CharField(_('title (Arabic)'), max_length=255, blank=True)
    
    message = models.TextField(_('message'))
    message_ar = models.TextField(_('message (Arabic)'), blank=True)
    
    # Status
    is_read = models.BooleanField(_('is read'), default=False)
    is_push_sent = models.BooleanField(_('is push sent'), default=False)
    
    # Action links
    action_url = models.URLField(_('action URL'), blank=True)
    action_text = models.CharField(_('action text'), max_length=50, blank=True)
    action_text_ar = models.CharField(_('action text (Arabic)'), max_length=50, blank=True)
    
    # Related objects
    ticket_sale = models.ForeignKey('TicketSale', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    submission = models.ForeignKey('SalesSubmission', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)

    class Meta:
        verbose_name = _('Finance Notification')
        verbose_name_plural = _('Finance Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    
    def get_title(self, language='en'):
        """Get title in specified language"""
        if language == 'ar' and self.title_ar:
            return self.title_ar
        return self.title
    
    def get_message(self, language='en'):
        """Get message in specified language"""
        if language == 'ar' and self.message_ar:
            return self.message_ar
        return self.message
    
    def get_action_text(self, language='en'):
        """Get action text in specified language"""
        if language == 'ar' and self.action_text_ar:
            return self.action_text_ar
        return self.action_text


class NotificationTemplate(models.Model):
    """Email notification templates"""
    
    template_type = models.CharField(_('template type'), max_length=50, unique=True)
    
    subject = models.CharField(_('subject'), max_length=255)
    subject_ar = models.CharField(_('subject (Arabic)'), max_length=255, blank=True)
    
    html_content = models.TextField(_('HTML content'))
    html_content_ar = models.TextField(_('HTML content (Arabic)'), blank=True)
    
    text_content = models.TextField(_('text content'), blank=True)
    text_content_ar = models.TextField(_('text content (Arabic)'), blank=True)
    
    is_active = models.BooleanField(_('is active'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        ordering = ['template_type']

    def __str__(self):
        return self.template_type
    
    def get_subject(self, language='en'):
        """Get subject in specified language"""
        if language == 'ar' and self.subject_ar:
            return self.subject_ar
        return self.subject
    
    def get_html_content(self, language='en'):
        """Get HTML content in specified language"""
        if language == 'ar' and self.html_content_ar:
            return self.html_content_ar
        return self.html_content
    
    def get_text_content(self, language='en'):
        """Get text content in specified language"""
        if language == 'ar' and self.text_content_ar:
            return self.text_content_ar
        return self.text_content
