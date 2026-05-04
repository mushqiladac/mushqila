from rest_framework import serializers
from ..models import FinanceTransaction, CreditSale
from ..models.transaction import PaymentInstallment


class FinanceTransactionSerializer(serializers.ModelSerializer):
    """Serializer for FinanceTransaction model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    ticket_number = serializers.CharField(source='ticket_sale.ticket_number', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FinanceTransaction
        fields = [
            'id', 'user', 'user_name', 'user_email', 'ticket_sale', 'ticket_number',
            'transaction_id', 'transaction_type', 'transaction_type_display',
            'amount', 'currency', 'status', 'status_display', 'description',
            'description_ar', 'reference', 'balance_before', 'balance_after',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'transaction_id', 'balance_before', 'balance_after',
            'created_at', 'updated_at'
        ]


class CreditSaleSerializer(serializers.ModelSerializer):
    """Serializer for CreditSale model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    ticket_number = serializers.CharField(source='ticket_sale.ticket_number', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CreditSale
        fields = [
            'id', 'user', 'user_name', 'user_email', 'ticket_sale', 'ticket_number',
            'total_amount', 'paid_amount', 'remaining_amount', 'due_date',
            'payment_status', 'payment_status_display', 'last_payment_date',
            'completed_date', 'notes', 'is_overdue', 'days_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_name', 'user_email', 'ticket_number',
            'remaining_amount', 'last_payment_date', 'completed_date',
            'is_overdue', 'days_overdue', 'created_at', 'updated_at'
        ]


class CreditSaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CreditSale"""
    
    class Meta:
        model = CreditSale
        fields = [
            'ticket_sale', 'total_amount', 'due_date', 'notes'
        ]
    
    def validate_ticket_sale(self, value):
        """Validate ticket sale"""
        if CreditSale.objects.filter(ticket_sale=value).exists():
            raise serializers.ValidationError("Credit sale already exists for this ticket")
        return value
    
    def validate(self, attrs):
        """Validate credit sale data"""
        total_amount = attrs.get('total_amount', 0)
        due_date = attrs.get('due_date')
        
        if total_amount <= 0:
            raise serializers.ValidationError("Total amount must be greater than 0")
        
        if not due_date:
            raise serializers.ValidationError("Due date is required")
        
        return attrs


class PaymentInstallmentSerializer(serializers.ModelSerializer):
    """Serializer for PaymentInstallment model"""
    
    is_overdue = serializers.BooleanField(read_only=True)
    days_overdue = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PaymentInstallment
        fields = [
            'id', 'credit_sale', 'installment_number', 'amount', 'due_date',
            'paid_amount', 'paid_date', 'is_paid', 'notes', 'is_overdue',
            'days_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'credit_sale', 'paid_amount', 'paid_date', 'is_paid',
            'is_overdue', 'days_overdue', 'created_at', 'updated_at'
        ]


class PaymentInstallmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PaymentInstallment"""
    
    class Meta:
        model = PaymentInstallment
        fields = [
            'installment_number', 'amount', 'due_date', 'notes'
        ]
    
    def validate(self, attrs):
        """Validate installment data"""
        credit_sale = self.context['credit_sale']
        installment_number = attrs.get('installment_number')
        amount = attrs.get('amount', 0)
        
        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        
        # Check if installment number already exists
        if PaymentInstallment.objects.filter(
            credit_sale=credit_sale,
            installment_number=installment_number
        ).exists():
            raise serializers.ValidationError("Installment number already exists")
        
        return attrs


class PaymentSerializer(serializers.Serializer):
    """Serializer for making payments"""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_method = serializers.CharField(max_length=50)
    reference = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False)
    
    def validate_amount(self, value):
        """Validate payment amount"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
