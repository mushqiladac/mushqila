from rest_framework import serializers
from ..models import SalesSubmission
from ..models.submission import SubmissionComment


class SubmissionCommentSerializer(serializers.ModelSerializer):
    """Serializer for SubmissionComment model"""
    
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_email = serializers.CharField(source='author.email', read_only=True)
    
    class Meta:
        model = SubmissionComment
        fields = [
            'id', 'author', 'author_name', 'author_email', 'comment',
            'is_internal', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'author_name', 'author_email', 'created_at', 'updated_at'
        ]


class SalesSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for SalesSubmission model (read-only)"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    ticket_number = serializers.CharField(source='ticket_sale.ticket_number', read_only=True)
    passenger_name = serializers.CharField(source='ticket_sale.passenger_name', read_only=True)
    total_amount = serializers.DecimalField(source='ticket_sale.total_amount', read_only=True, max_digits=12, decimal_places=2)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    comments = SubmissionCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = SalesSubmission
        fields = [
            'id', 'user', 'user_name', 'user_email', 'ticket_sale', 'ticket_number',
            'passenger_name', 'total_amount', 'submitted_at', 'reviewed_at',
            'reviewed_by', 'reviewed_by_name', 'status', 'status_display',
            'manager_notes', 'rejection_reason', 'user_response', 'revised_at',
            'metadata', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_name', 'user_email', 'ticket_number',
            'passenger_name', 'total_amount', 'submitted_at', 'reviewed_at',
            'reviewed_by', 'reviewed_by_name', 'created_at', 'updated_at'
        ]


class SalesSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SalesSubmission"""
    
    class Meta:
        model = SalesSubmission
        fields = ['ticket_sale']
    
    def validate_ticket_sale(self, value):
        """Validate ticket sale"""
        user = self.context['request'].user
        
        # Check if ticket belongs to user
        if value.user != user:
            raise serializers.ValidationError("Ticket sale does not belong to you")
        
        # Check if submission already exists
        if SalesSubmission.objects.filter(ticket_sale=value).exists():
            raise serializers.ValidationError("Submission already exists for this ticket")
        
        return value


class SubmissionReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviewing submissions (manager only)"""
    
    class Meta:
        model = SalesSubmission
        fields = ['status', 'manager_notes', 'rejection_reason']
    
    def validate(self, attrs):
        """Validate review data"""
        status = attrs.get('status')
        manager_notes = attrs.get('manager_notes', '')
        rejection_reason = attrs.get('rejection_reason', '')
        
        if status == SalesSubmission.SubmissionStatus.REJECTED and not rejection_reason:
            raise serializers.ValidationError("Rejection reason is required when rejecting")
        
        if status == SalesSubmission.SubmissionStatus.REVISION_REQUIRED and not manager_notes:
            raise serializers.ValidationError("Manager notes are required when requesting revision")
        
        return attrs


class SubmissionResubmitSerializer(serializers.ModelSerializer):
    """Serializer for resubmitting after revision"""
    
    class Meta:
        model = SalesSubmission
        fields = ['user_response']
    
    def validate_user_response(self, value):
        """Validate user response"""
        if not value.strip():
            raise serializers.ValidationError("User response is required")
        return value


class SubmissionCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating submission comments"""
    
    class Meta:
        model = SubmissionComment
        fields = ['comment', 'is_internal']
    
    def validate_comment(self, value):
        """Validate comment text"""
        if not value.strip():
            raise serializers.ValidationError("Comment text is required")
        return value
    
    def validate_is_internal(self, value):
        """Validate internal comment permission"""
        user = self.context['request'].user
        if value and user.user_type != FinanceUser.UserType.MANAGER:
            raise serializers.ValidationError("Only managers can add internal comments")
        return value
