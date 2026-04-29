from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum


class Airline(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=100, blank=True)
    settlement_days = models.PositiveIntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Sale(models.Model):
    class SaleStatus(models.TextChoices):
        ISSUED = "issued", "Issued"
        VOID = "void", "Void"
        REFUND = "refund", "Refund"
        REISSUE = "reissue", "Reissue"

    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name="sales")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales")

    pnr = models.CharField(max_length=20)
    ticket_number = models.CharField(max_length=30, unique=True)
    issue_date = models.DateField()
    travel_date = models.DateField(null=True, blank=True)
    route = models.CharField(max_length=120, blank=True)
    passenger_name = models.CharField(max_length=120)

    base_fare = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    other_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    customer_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    airline_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    currency = models.CharField(max_length=3, default="SAR")

    status = models.CharField(max_length=15, choices=SaleStatus.choices, default=SaleStatus.ISSUED)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-id"]
        indexes = [
            models.Index(fields=["issue_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["user", "issue_date"]),
        ]

    def __str__(self):
        return f"{self.ticket_number} ({self.status})"

    @property
    def gross_amount(self):
        return self.base_fare + self.tax_amount + self.other_fee

    @property
    def due_amount(self):
        allocated_total = self.payment_allocations.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        return self.customer_price - allocated_total


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CARD = "card", "Card"
        ADJUSTMENT = "adjustment", "Adjustment"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    airline = models.ForeignKey(Airline, on_delete=models.PROTECT, related_name="payments")
    received_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.BANK_TRANSFER)
    reference_no = models.CharField(max_length=60, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_date", "-id"]

    def __str__(self):
        return f"{self.user_id} - {self.amount}"


class PaymentAllocation(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="allocations")
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payment_allocations")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("payment", "sale")

    def __str__(self):
        return f"{self.payment_id} -> {self.sale_id} ({self.amount})"


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounting_audit_logs",
    )
    action = models.CharField(max_length=40)
    entity = models.CharField(max_length=40)
    entity_id = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity", "entity_id"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.entity}#{self.entity_id}"
