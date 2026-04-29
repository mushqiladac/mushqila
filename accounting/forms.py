from django import forms

from .models import Payment, PaymentAllocation, Sale


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = [
            "user",
            "airline",
            "pnr",
            "ticket_number",
            "issue_date",
            "travel_date",
            "route",
            "passenger_name",
            "base_fare",
            "tax_amount",
            "other_fee",
            "commission_amount",
            "customer_price",
            "airline_cost",
            "currency",
            "status",
            "remarks",
        ]
        widgets = {
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "travel_date": forms.DateInput(attrs={"type": "date"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["user", "airline", "received_date", "amount", "payment_method", "reference_no", "notes"]
        widgets = {
            "received_date": forms.DateInput(attrs={"type": "date"}),
        }


class PaymentAllocationForm(forms.ModelForm):
    class Meta:
        model = PaymentAllocation
        fields = ["payment", "sale", "amount"]
