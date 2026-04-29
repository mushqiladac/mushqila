from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from .models import Airline, AuditLog, Payment, PaymentAllocation, Sale


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = "__all__"


class SaleSerializer(serializers.ModelSerializer):
    due_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = "__all__"


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"


class PaymentAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAllocation
        fields = "__all__"

    def validate(self, attrs):
        payment = attrs.get("payment") or self.instance.payment
        sale = attrs.get("sale") or self.instance.sale
        amount = attrs.get("amount") if attrs.get("amount") is not None else self.instance.amount

        allocated_total = payment.allocations.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        if self.instance and self.instance.payment_id == payment.id:
            allocated_total -= self.instance.amount
        if allocated_total + amount > payment.amount:
            raise serializers.ValidationError({"amount": "Allocated amount exceeds payment amount."})

        if sale.due_amount < amount:
            raise serializers.ValidationError({"amount": "Allocation amount exceeds sale due."})

        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = "__all__"
