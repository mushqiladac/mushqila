from rest_framework import serializers
from ..models import TicketSale, Airline, PaymentMethod


class AirlineSerializer(serializers.ModelSerializer):
    """Serializer for Airline model"""
    
    class Meta:
        model = Airline
        fields = ['id', 'code', 'name', 'name_ar', 'country', 'is_active']
        read_only_fields = ['id']


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for PaymentMethod model"""
    
    method_display = serializers.CharField(source='get_name_display', read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'name_ar', 'description', 'is_active', 'method_display']
        read_only_fields = ['id']


class TicketSaleSerializer(serializers.ModelSerializer):
    """Serializer for TicketSale model (read-only)"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    airline_name = serializers.CharField(source='airline.name', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.get_name_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sale_type_display = serializers.CharField(source='get_sale_type_display', read_only=True)
    profit_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = TicketSale
        fields = [
            'id', 'user', 'user_name', 'user_email', 'airline', 'airline_name',
            'payment_method', 'payment_method_name', 'pnr', 'ticket_number',
            'passenger_name', 'route', 'travel_date', 'purchase_price', 'selling_price',
            'commission_amount', 'tax_amount', 'sale_type', 'sale_type_display',
            'status', 'status_display', 'deposit_amount', 'due_amount', 'due_date',
            'remarks', 'reference_number', 'issue_date', 'created_at', 'updated_at',
            'profit_amount', 'total_amount'
        ]
        read_only_fields = [
            'id', 'user', 'user_name', 'user_email', 'airline_name',
            'payment_method_name', 'profit_amount', 'total_amount',
            'created_at', 'updated_at'
        ]


class TicketSaleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating TicketSale"""
    
    class Meta:
        model = TicketSale
        fields = [
            'airline', 'payment_method', 'pnr', 'ticket_number',
            'passenger_name', 'route', 'travel_date', 'purchase_price',
            'selling_price', 'commission_amount', 'tax_amount',
            'sale_type', 'deposit_amount', 'due_date', 'remarks',
            'reference_number'
        ]
    
    def validate_ticket_number(self, value):
        """Validate ticket number uniqueness"""
        if TicketSale.objects.filter(ticket_number=value).exists():
            raise serializers.ValidationError("Ticket number already exists")
        return value
    
    def validate(self, attrs):
        """Validate ticket sale data"""
        purchase_price = attrs.get('purchase_price', 0)
        selling_price = attrs.get('selling_price', 0)
        sale_type = attrs.get('sale_type')
        
        if selling_price <= 0:
            raise serializers.ValidationError("Selling price must be greater than 0")
        
        if purchase_price <= 0:
            raise serializers.ValidationError("Purchase price must be greater than 0")
        
        # For credit sales, validate deposit and due date
        if sale_type == TicketSale.SaleType.CREDIT:
            deposit_amount = attrs.get('deposit_amount', 0)
            due_date = attrs.get('due_date')
            
            if not due_date:
                raise serializers.ValidationError("Due date is required for credit sales")
            
            if deposit_amount and deposit_amount >= selling_price:
                raise serializers.ValidationError("Deposit amount must be less than selling price")
        
        return attrs
    
    def create(self, validated_data):
        """Create ticket sale"""
        user = self.context['request'].user
        
        # Set initial status based on user type
        if user.user_type == FinanceUser.UserType.MANAGER:
            validated_data['status'] = TicketSale.SaleStatus.APPROVED
        else:
            validated_data['status'] = TicketSale.SaleStatus.PENDING
        
        return TicketSale.objects.create(user=user, **validated_data)


class TicketSaleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating TicketSale"""
    
    class Meta:
        model = TicketSale
        fields = [
            'airline', 'payment_method', 'pnr', 'passenger_name', 'route',
            'travel_date', 'purchase_price', 'selling_price', 'commission_amount',
            'tax_amount', 'sale_type', 'deposit_amount', 'due_date',
            'remarks', 'reference_number'
        ]
    
    def validate_ticket_number(self, value):
        """Validate ticket number uniqueness on update"""
        instance = self.instance
        if TicketSale.objects.exclude(id=instance.id).filter(ticket_number=value).exists():
            raise serializers.ValidationError("Ticket number already exists")
        return value
