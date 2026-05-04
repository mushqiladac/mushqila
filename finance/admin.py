from django.contrib import admin
from .models.user import FinanceUser, FinanceUserProfile
from .models.ticket import TicketSale, Airline, PaymentMethod
from .models.transaction import FinanceTransaction, CreditSale, PaymentInstallment
from .models.submission import SalesSubmission, SubmissionComment
from .models.notification import FinanceNotification, NotificationTemplate


@admin.register(FinanceUser)
class FinanceUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'get_full_name', 'user_type', 'status', 'current_balance', 'date_joined']
    list_filter = ['user_type', 'status', 'email_verified', 'phone_verified']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    readonly_fields = ['id', 'date_joined', 'last_login']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone', 'alternative_email')
        }),
        ('User Details', {
            'fields': ('user_type', 'status', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Financial Information', {
            'fields': ('credit_limit', 'current_balance', 'total_sales')
        }),
        ('Verification', {
            'fields': ('email_verified', 'phone_verified')
        }),
        ('Security', {
            'fields': ('otp_code', 'otp_expires_at')
        }),
        ('Timestamps', {
            'fields': ('last_login', 'last_login_ip', 'created_at', 'updated_at')
        })
    )


@admin.register(FinanceUserProfile)
class FinanceUserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'language', 'total_tickets_sold', 'total_commission']
    search_fields = ['user__email', 'company_name', 'bank_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'country', 'is_active', 'created_at']
    list_filter = ['is_active', 'country']
    search_fields = ['code', 'name', 'name_ar']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_ar', 'is_active', 'created_at']
    list_filter = ['is_active', 'name']
    search_fields = ['name', 'name_ar', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TicketSale)
class TicketSaleAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'passenger_name', 'user', 'airline', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'sale_type', 'payment_method', 'airline', 'created_at']
    search_fields = ['ticket_number', 'pnr', 'passenger_name', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'profit_amount', 'total_amount']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'airline', 'payment_method', 'pnr', 'ticket_number', 'passenger_name')
        }),
        ('Flight Details', {
            'fields': ('route', 'travel_date', 'issue_date')
        }),
        ('Financial Details', {
            'fields': ('purchase_price', 'selling_price', 'commission_amount', 'tax_amount')
        }),
        ('Sale Information', {
            'fields': ('sale_type', 'status')
        }),
        ('Credit Sale Details', {
            'fields': ('deposit_amount', 'due_amount', 'due_date')
        }),
        ('Additional Information', {
            'fields': ('remarks', 'reference_number')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'profit_amount', 'total_amount')
        })
    )


@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['transaction_id', 'user__email', 'description']
    readonly_fields = ['id', 'transaction_id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = ['ticket_sale', 'user', 'total_amount', 'paid_amount', 'remaining_amount', 'payment_status', 'due_date']
    list_filter = ['payment_status', 'due_date', 'created_at']
    search_fields = ['ticket_sale__ticket_number', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(PaymentInstallment)
class PaymentInstallmentAdmin(admin.ModelAdmin):
    list_display = ['credit_sale', 'installment_number', 'amount', 'due_date', 'paid_amount', 'is_paid']
    list_filter = ['is_paid', 'due_date']
    search_fields = ['credit_sale__ticket_sale__ticket_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['credit_sale', 'installment_number']


@admin.register(SalesSubmission)
class SalesSubmissionAdmin(admin.ModelAdmin):
    list_display = ['ticket_sale', 'user', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at']
    list_filter = ['status', 'submitted_at', 'reviewed_at']
    search_fields = ['ticket_sale__ticket_number', 'user__email']
    readonly_fields = ['id', 'submitted_at', 'created_at', 'updated_at']
    ordering = ['-submitted_at']


@admin.register(SubmissionComment)
class SubmissionCommentAdmin(admin.ModelAdmin):
    list_display = ['submission', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['submission__ticket_sale__ticket_number', 'author__email', 'comment']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(FinanceNotification)
class FinanceNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_type', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'template_type']
    search_fields = ['template_type', 'subject', 'subject_ar']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['template_type']
