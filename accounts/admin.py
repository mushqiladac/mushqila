"""
Admin configurations for B2B Travel Platform - Saudi Arabia
Fixed according to available models
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from .models import (
    # Core models
    User, UserProfile, Transaction, Notification, UserActivityLog,
    SaudiRegion, SaudiCity,
    
    # Business models
    Document, LoginHistory, AgentHierarchy, CreditRequest,
    SMSCode, IPWhitelist, ComplianceCheck,
    
    # Financial models
    Payment, Invoice, Refund, CommissionTransaction,
    
    # Travel models
    ServiceSupplier, FlightBooking, HotelBooking, HajjPackage, UmrahPackage,
)


# Custom filters
class SaudiRegionFilter(SimpleListFilter):
    """Filter users by Saudi region"""
    title = _('Saudi Region')
    parameter_name = 'region'
    
    def lookups(self, request, model_admin):
        regions = SaudiRegion.objects.filter(is_active=True)
        return [(region.id, region.name_en) for region in regions]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(city__region_id=self.value())
        return queryset


class UserTypeFilter(SimpleListFilter):
    """Filter by user type"""
    title = _('User Type')
    parameter_name = 'user_type'
    
    def lookups(self, request, model_admin):
        return User.UserType.choices
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user_type=self.value())
        return queryset


class StatusFilter(SimpleListFilter):
    """Filter by user status"""
    title = _('Status')
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return User.Status.choices
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class KYCStatusFilter(SimpleListFilter):
    """Filter by KYC verification status"""
    title = _('KYC Status')
    parameter_name = 'kyc_status'
    
    def lookups(self, request, model_admin):
        return [
            ('verified', _('Verified')),
            ('pending', _('Pending')),
            ('not_submitted', _('Not Submitted')),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'verified':
            return queryset.filter(kyc_verified=True)
        elif self.value() == 'pending':
            return queryset.filter(kyc_verified=False, kyc_submitted__isnull=False)
        elif self.value() == 'not_submitted':
            return queryset.filter(kyc_submitted__isnull=True)
        return queryset


# Inline admins
class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('User Profile')
    fk_name = 'user'
    fields = ['business_type', 'years_in_business', 'total_bookings', 'total_sales']


class DocumentInline(admin.TabularInline):
    """Inline admin for Documents"""
    model = Document
    extra = 0
    fields = ['document_type', 'document_number', 'status', 'expiry_date', 'created_at']
    readonly_fields = ['created_at']


# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model with Saudi Arabia specific features"""
    
    inlines = [UserProfileInline]
    list_display = [
        'email', 'get_full_name', 'company_name_en', 
        'user_type', 'status', 'kyc_verified', 'city',
        'credit_limit', 'wallet_balance', 'is_active', 'created_at'
    ]
    list_filter = [
        UserTypeFilter, StatusFilter, KYCStatusFilter, 
        SaudiRegionFilter, 'is_active', 'email_verified', 'phone_verified'
    ]
    search_fields = [
        'email', 'first_name', 'last_name', 'phone',
        'company_name_ar', 'company_name_en', 'company_registration'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login_ip', 'last_activity', 'referral_code']
    filter_horizontal = ['groups', 'user_permissions']
    
    fieldsets = (
        (_('Authentication'), {
            'fields': ('email', 'password', 'username')
        }),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name')
        }),
        (_('Contact Info - Saudi Arabia'), {
            'fields': ('phone', 'email_verified', 'phone_verified',
                      'address_ar', 'address_en', 'city')
        }),
        (_('Company Info - Saudi Arabia'), {
            'fields': ('company_name_ar', 'company_name_en',
                      'company_registration', 'vat_number',
                      'scta_license', 'hajj_license', 'iata_number')
        }),
        (_('Financial Info - Saudi Arabia'), {
            'fields': ('commission_rate', 'credit_limit', 
                      'current_balance', 'wallet_balance',
                      'referral_code', 'referred_by')
        }),
        (_('Account Status'), {
            'fields': ('user_type', 'status', 'is_active', 'is_staff', 'is_superuser',
                      'kyc_verified', 'kyc_submitted')
        }),
        (_('Security & Activity'), {
            'fields': ('last_login', 'last_login_ip', 'last_activity',
                      'created_at', 'updated_at')
        }),
        (_('Permissions'), {
            'fields': ('groups', 'user_permissions')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone',
                      'company_name_en', 'company_registration', 'user_type',
                      'password1', 'password2'),
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Full Name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('city', 'city__region')


# Other admin configurations
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile"""
    list_display = ['user', 'business_type', 'years_in_business', 
                   'total_bookings', 'total_sales', 'total_commission']
    search_fields = ['user__email', 'user__company_name_en']
    list_filter = ['business_type', 'language']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin for Transaction"""
    list_display = ['transaction_id', 'user', 'amount', 'currency',
                   'transaction_type', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'currency', 'created_at']
    search_fields = ['transaction_id', 'user__email', 'reference']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin for Document"""
    list_display = ['user', 'document_type', 'document_number', 
                   'status', 'expiry_date', 'created_at']
    list_filter = ['document_type', 'status']
    search_fields = ['user__email', 'document_number']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    actions = ['mark_as_verified', 'mark_as_rejected']
    
    def mark_as_verified(self, request, queryset):
        queryset.update(status='verified', verified_by=request.user, 
                       verified_at=timezone.now())
    mark_as_verified.short_description = _("Mark selected documents as verified")
    
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
    mark_as_rejected.short_description = _("Mark selected documents as rejected")


@admin.register(SaudiRegion)
class SaudiRegionAdmin(admin.ModelAdmin):
    """Admin for SaudiRegion"""
    list_display = ['region_code', 'name_en', 'name_ar', 
                   'capital_en', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name_en', 'name_ar', 'region_code']


@admin.register(SaudiCity)
class SaudiCityAdmin(admin.ModelAdmin):
    """Admin for SaudiCity"""
    list_display = ['name_en', 'name_ar', 'region', 'postal_code',
                   'is_major_city', 'is_hajj_city', 'is_umrah_city', 'is_active']
    list_filter = ['region', 'is_major_city', 'is_hajj_city', 
                  'is_umrah_city', 'is_active']
    search_fields = ['name_en', 'name_ar', 'postal_code']


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin for LoginHistory"""
    list_display = ['user', 'ip_address', 'country_code', 
                   'success', 'failure_reason', 'created_at']
    list_filter = ['success', 'country_code']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification"""
    list_display = ['user', 'notification_type', 'title', 
                   'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Admin for UserActivityLog"""
    list_display = ['user', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type']
    search_fields = ['user__email', 'description', 'ip_address']
    readonly_fields = ['created_at']


@admin.register(AgentHierarchy)
class AgentHierarchyAdmin(admin.ModelAdmin):
    """Admin for AgentHierarchy"""
    list_display = ['parent_agent', 'child_agent', 'hierarchy_level',
                   'commission_share', 'is_active']
    list_filter = ['is_active', 'hierarchy_level']
    search_fields = ['parent_agent__email', 'child_agent__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CreditRequest)
class CreditRequestAdmin(admin.ModelAdmin):
    """Admin for CreditRequest"""
    list_display = ['user', 'current_limit', 'requested_limit',
                   'status', 'reviewed_by', 'created_at']
    list_filter = ['status']
    search_fields = ['user__email', 'purpose']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        updated = 0
        for credit_request in queryset:
            if credit_request.can_be_approved():
                credit_request.status = 'approved'
                credit_request.reviewed_by = request.user
                credit_request.approved_at = timezone.now()
                credit_request.save()
                
                # Update user's credit limit
                user = credit_request.user
                user.credit_limit = credit_request.requested_limit
                user.save()
                updated += 1
        
        if updated:
            self.message_user(request, f"{updated} credit requests approved successfully.")
    approve_requests.short_description = _("Approve selected credit requests")
    
    def reject_requests(self, request, queryset):
        queryset.update(status='rejected', reviewed_by=request.user)
        self.message_user(request, f"{queryset.count()} credit requests rejected.")
    reject_requests.short_description = _("Reject selected credit requests")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment"""
    list_display = ['payment_id', 'user', 'total_amount', 'payment_method',
                   'status', 'created_at', 'completed_at']
    list_filter = ['payment_method', 'status']
    search_fields = ['payment_id', 'user__email', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin for Invoice"""
    list_display = ['invoice_number', 'user', 'total_amount', 'paid_amount',
                   'status', 'issue_date', 'due_date', 'payment_date']
    list_filter = ['status']
    search_fields = ['invoice_number', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'issue_date'
    actions = ['mark_as_paid']
    
    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid', payment_date=timezone.now())
    mark_as_paid.short_description = _("Mark selected invoices as paid")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Admin for Refund"""
    list_display = ['refund_id', 'user', 'refund_amount', 'refund_method',
                   'status', 'requested_at', 'processed_at']
    list_filter = ['refund_method', 'status']
    search_fields = ['refund_id', 'user__email']
    readonly_fields = ['requested_at', 'approved_at', 'processed_at']
    date_hierarchy = 'requested_at'


@admin.register(CommissionTransaction)
class CommissionTransactionAdmin(admin.ModelAdmin):
    """Admin for CommissionTransaction"""
    list_display = ['transaction_id', 'agent', 'amount', 'commission_rate',
                   'status', 'payment_date', 'created_at']
    list_filter = ['status']
    search_fields = ['transaction_id', 'agent__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(ServiceSupplier)
class ServiceSupplierAdmin(admin.ModelAdmin):
    """Admin for ServiceSupplier"""
    list_display = ['name', 'supplier_type', 'code', 'commission_rate',
                   'is_active', 'created_at']
    list_filter = ['supplier_type', 'is_active']
    search_fields = ['name', 'code', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FlightBooking)
class FlightBookingAdmin(admin.ModelAdmin):
    """Admin for FlightBooking"""
    list_display = ['booking_id', 'agent', 'passenger_name', 'airline',
                   'departure_city', 'arrival_city', 'departure_date',
                   'total_amount', 'status', 'created_at']
    list_filter = ['status', 'travel_type']
    search_fields = ['booking_id', 'passenger_name', 'agent__email', 'pnr']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    """Admin for HotelBooking"""
    list_display = ['booking_id', 'agent', 'guest_name', 'hotel',
                   'check_in', 'check_out', 'nights', 'rooms',
                   'total_amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['booking_id', 'guest_name', 'agent__email', 'confirmation_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(HajjPackage)
class HajjPackageAdmin(admin.ModelAdmin):
    """Admin for HajjPackage"""
    list_display = ['package_code', 'name', 'hajj_year', 'duration_days',
                   'base_price', 'commission_rate', 'available_slots',
                   'status', 'created_at']
    list_filter = ['status', 'hajj_year']
    search_fields = ['package_code', 'name', 'name_ar']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UmrahPackage)
class UmrahPackageAdmin(admin.ModelAdmin):
    """Admin for UmrahPackage"""
    list_display = ['package_code', 'name', 'package_type', 'duration_days',
                   'validity_from', 'validity_to', 'base_price',
                   'commission_rate', 'created_at']
    list_filter = ['package_type']
    search_fields = ['package_code', 'name', 'name_ar']
    readonly_fields = ['created_at', 'updated_at']


# Simple register for remaining models
@admin.register(SMSCode)
class SMSCodeAdmin(admin.ModelAdmin):
    list_display = ['phone', 'code', 'purpose', 'is_used', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used']
    search_fields = ['phone']
    readonly_fields = ['created_at']


@admin.register(IPWhitelist)
class IPWhitelistAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'description', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ['user', 'check_type', 'status', 'score', 'performed_at', 'created_at']
    list_filter = ['check_type', 'status']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at', 'performed_at']


# Admin site customization
admin.site.site_header = _("Mushqila Saudi Arabia - B2B Travel Platform")
admin.site.site_title = _("Mushqila Admin")
admin.site.index_title = _("Welcome to Mushqila Saudi Arabia Administration")