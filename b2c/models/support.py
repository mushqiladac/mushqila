"""B2C Support Models - Placeholder"""
from django.db import models
from .customer import Customer

class SupportTicket(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    ticket_number = models.CharField(max_length=50, unique=True)
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=20, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_support_ticket'

class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_ticket_message'

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE)
    file = models.FileField(upload_to='tickets/')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_ticket_attachment'

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'b2c_faq'
