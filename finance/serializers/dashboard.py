from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    
    user_info = serializers.DictField()
    statistics = serializers.DictField()
    breakdowns = serializers.DictField()
    credit_info = serializers.DictField()
    recent_activity = serializers.ListField()


class SalesChartSerializer(serializers.Serializer):
    """Serializer for sales chart data"""
    
    period = serializers.CharField()
    daily_data = serializers.ListField(child=serializers.DictField())


class TopPerformerSerializer(serializers.Serializer):
    """Serializer for top performers data"""
    
    user_id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_tickets = serializers.IntegerField()
    total_commission = serializers.DecimalField(max_digits=15, decimal_places=2)


class PendingTaskSerializer(serializers.Serializer):
    """Serializer for pending tasks"""
    
    type = serializers.CharField()
    title = serializers.CharField()
    count = serializers.IntegerField()
    priority = serializers.CharField()


class NotificationListSerializer(serializers.Serializer):
    """Serializer for notification list"""
    
    id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    is_read = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    action_url = serializers.URLField(required=False, allow_blank=True)
    action_text = serializers.CharField(required=False, allow_blank=True)


class TransactionSummarySerializer(serializers.Serializer):
    """Serializer for transaction summary"""
    
    total = serializers.DictField()
    by_type = serializers.ListField(child=serializers.DictField())
    by_status = serializers.ListField(child=serializers.DictField())
    filter = serializers.CharField()


class BalanceHistorySerializer(serializers.Serializer):
    """Serializer for balance history"""
    
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    history = serializers.ListField(child=serializers.DictField())


class CreditSummarySerializer(serializers.Serializer):
    """Serializer for credit summary"""
    
    summary = serializers.DictField()
    status_breakdown = serializers.ListField(child=serializers.DictField())


class SubmissionStatsSerializer(serializers.Serializer):
    """Serializer for submission statistics"""
    
    status_breakdown = serializers.ListField(child=serializers.DictField())
    total_submissions = serializers.IntegerField()
    approved_submissions = serializers.IntegerField()
    approval_rate = serializers.FloatField()
    recent_submissions = serializers.ListField(child=serializers.DictField())


class SubmissionHistorySerializer(serializers.Serializer):
    """Serializer for submission history"""
    
    daily_data = serializers.ListField(child=serializers.DictField())
