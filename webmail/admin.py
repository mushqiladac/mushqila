from django.contrib import admin
from .models import (
    EmailAccount, Email, EmailAttachment, EmailLabel,
    EmailLabelAssignment, EmailFilter, EmailTemplate, Contact
)


@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ['email_address', 'display_name', 'user', 'ses_verified', 'is_default', 'is_active', 'created_at']
    list_filter = ['ses_verified', 'is_default', 'is_active', 'created_at']
    search_fields = ['email_address', 'display_name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'email_address', 'display_name', 'signature')
        }),
        ('AWS SES Configuration', {
            'fields': ('aws_access_key', 'aws_secret_key', 'aws_region', 'ses_verified')
        }),
        ('AWS S3 Configuration', {
            'fields': ('s3_bucket_name', 's3_inbox_prefix')
        }),
        ('Settings', {
            'fields': ('is_default', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'from_address', 'account', 'folder', 'is_read', 'is_starred', 'received_at']
    list_filter = ['folder', 'is_read', 'is_starred', 'is_important', 'is_draft', 'received_at']
    search_fields = ['subject', 'from_address', 'to_addresses', 'body_text']
    readonly_fields = ['message_id', 'created_at', 'updated_at', 'read_at']
    date_hierarchy = 'received_at'
    
    fieldsets = (
        ('Email Information', {
            'fields': ('account', 'message_id', 'subject')
        }),
        ('Addresses', {
            'fields': ('from_address', 'from_name', 'to_addresses', 'cc_addresses', 'bcc_addresses', 'reply_to')
        }),
        ('Content', {
            'fields': ('body_text', 'body_html')
        }),
        ('S3 Storage', {
            'fields': ('s3_key', 's3_url'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('folder', 'is_read', 'is_starred', 'is_important', 'is_draft')
        }),
        ('Thread', {
            'fields': ('thread_id', 'in_reply_to', 'references'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'received_at', 'read_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'email', 'content_type', 'size_bytes', 'is_inline', 'created_at']
    list_filter = ['content_type', 'is_inline', 'created_at']
    search_fields = ['filename', 'email__subject']
    readonly_fields = ['id', 'created_at']


@admin.register(EmailLabel)
class EmailLabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'color', 'created_at']
    list_filter = ['account', 'created_at']
    search_fields = ['name']


@admin.register(EmailLabelAssignment)
class EmailLabelAssignmentAdmin(admin.ModelAdmin):
    list_display = ['email', 'label', 'created_at']
    list_filter = ['label', 'created_at']
    search_fields = ['email__subject', 'label__name']


@admin.register(EmailFilter)
class EmailFilterAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'condition_field', 'action_type', 'is_active', 'priority']
    list_filter = ['is_active', 'condition_field', 'action_type', 'created_at']
    search_fields = ['name', 'condition_value']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('account', 'name', 'is_active', 'priority')
        }),
        ('Condition', {
            'fields': ('condition_field', 'condition_operator', 'condition_value')
        }),
        ('Action', {
            'fields': ('action_type', 'action_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'account', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'account', 'created_at']
    search_fields = ['name', 'subject', 'body_text']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('account', 'name', 'is_active')
        }),
        ('Email Content', {
            'fields': ('subject', 'body_html', 'body_text')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'user', 'email_count', 'is_favorite', 'last_emailed']
    list_filter = ['is_favorite', 'created_at', 'last_emailed']
    search_fields = ['email', 'name', 'company']
    readonly_fields = ['email_count', 'last_emailed', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('user', 'email', 'name', 'company', 'phone', 'notes')
        }),
        ('Statistics', {
            'fields': ('email_count', 'last_emailed', 'is_favorite')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
