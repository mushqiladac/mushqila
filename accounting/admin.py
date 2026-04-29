from django.contrib import admin

from .models import Airline, AuditLog, Payment, PaymentAllocation, Sale


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "pnr", "airline", "user", "customer_price", "status", "issue_date")
    search_fields = ("ticket_number", "pnr", "passenger_name")
    list_filter = ("status", "airline")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "airline", "amount", "payment_method", "received_date")
    list_filter = ("payment_method", "airline")


@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    list_display = ("payment", "sale", "amount", "created_at")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity", "entity_id", "actor", "created_at")
    list_filter = ("action", "entity")
    search_fields = ("entity_id", "description")
