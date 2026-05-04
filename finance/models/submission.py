from django.db import models
from django.utils.translation import gettext_lazy as _


class SalesSubmission(models.Model):
    """Sales submission for manager approval"""
    
    class SubmissionStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        REVISION_REQUIRED = 'revision_required', _('Revision Required')
    
    # Basic Information
    user = models.ForeignKey('FinanceUser', on_delete=models.CASCADE, related_name='sales_submissions')
    ticket_sale = models.OneToOneField('TicketSale', on_delete=models.CASCADE, related_name='submission')
    
    # Approval tracking
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    reviewed_at = models.DateTimeField(_('reviewed at'), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'FinanceUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_submissions'
    )
    
    # Status and decisions
    status = models.CharField(_('status'), max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.PENDING)
    
    # Manager feedback
    manager_notes = models.TextField(_('manager notes'), blank=True)
    rejection_reason = models.TextField(_('rejection reason'), blank=True)
    
    # User response to revision
    user_response = models.TextField(_('user response'), blank=True)
    revised_at = models.DateTimeField(_('revised at'), null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(_('metadata'), default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Sales Submission')
        verbose_name_plural = _('Sales Submissions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return f"Submission - {self.ticket_sale.ticket_number} ({self.get_status_display()})"
    
    @property
    def is_approved(self):
        """Check if submission is approved"""
        return self.status == self.SubmissionStatus.APPROVED
    
    @property
    def is_pending(self):
        """Check if submission is pending"""
        return self.status == self.SubmissionStatus.PENDING
    
    @property
    def needs_revision(self):
        """Check if submission needs revision"""
        return self.status == self.SubmissionStatus.REVISION_REQUIRED
    
    def approve(self, reviewer, notes=''):
        """Approve the submission"""
        self.status = self.SubmissionStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.manager_notes = notes
        self.ticket_sale.status = TicketSale.SaleStatus.APPROVED
        self.ticket_sale.save()
        self.save()
    
    def reject(self, reviewer, reason=''):
        """Reject the submission"""
        self.status = self.SubmissionStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.ticket_sale.status = TicketSale.SaleStatus.REJECTED
        self.ticket_sale.save()
        self.save()
    
    def request_revision(self, reviewer, notes=''):
        """Request revision for the submission"""
        self.status = self.SubmissionStatus.REVISION_REQUIRED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.manager_notes = notes
        self.save()
    
    def resubmit(self, response=''):
        """Resubmit after revision"""
        self.status = self.SubmissionStatus.PENDING
        self.user_response = response
        self.revised_at = timezone.now()
        self.reviewed_by = None
        self.reviewed_at = None
        self.manager_notes = ''
        self.rejection_reason = ''
        self.save()


class SubmissionComment(models.Model):
    """Comments on sales submissions"""
    
    submission = models.ForeignKey(SalesSubmission, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('FinanceUser', on_delete=models.CASCADE, related_name='submission_comments')
    
    comment = models.TextField(_('comment'))
    is_internal = models.BooleanField(_('internal comment'), default=False)  # Only visible to managers
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Submission Comment')
        verbose_name_plural = _('Submission Comments')
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.submission.ticket_sale.ticket_number}"
