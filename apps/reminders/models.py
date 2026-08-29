"""
Reminder models for Event Planner project.
"""

import html

from django.db import models

from apps.common.models import BaseModel


class Reminder(BaseModel):
    """
    Reminder model for scheduled notifications.
    """

    TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='reminders',
    )
    reminder_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    scheduled_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"Reminder for Booking #{self.booking.id} at {self.scheduled_at}"

    @property
    def can_send(self):
        """
        Check if reminder can be sent.
        """
        return self.status == 'pending'

    def mark_sent(self):
        """
        Mark reminder as sent.
        """
        from django.utils import timezone
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])

    def mark_failed(self, error_message=''):
        """
        Mark reminder as failed.
        """
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])


class ReminderTemplate(models.Model):
    """
    Template for reminder messages.
    """

    TYPE_CHOICES = [
        ('event_reminder', 'Event Reminder'),
        ('payment_reminder', 'Payment Reminder'),
        ('followup', 'Follow-up'),
        ('confirmation', 'Confirmation'),
    ]

    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='reminder_templates',
    )
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField(help_text="Message template with placeholders")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['business', 'template_type']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def render(self, booking):
        """
        Render template with booking data.
        """
        client = booking.client
        business = booking.business
        package = booking.package

        context = {
            'client_name': client.name,
            'event_date': booking.event_date.strftime('%B %d, %Y'),
            'event_time': booking.event_time.strftime('%I:%M %p') if booking.event_time else '',
            'venue': booking.venue,
            'package_name': package.name if package else 'Custom Package',
            'total_amount': f"{booking.total_amount:,.2f}",
            'balance_amount': f"{booking.balance_amount:,.2f}",
            'business_name': business.name,
            'business_phone': business.phone,
            'business_email': business.email,
        }

        content = self.content
        subject = self.subject

        for key, value in context.items():
            escaped = html.escape(str(value))
            content = content.replace(f'{{{{{key}}}}}', escaped)
            subject = subject.replace(f'{{{{{key}}}}}', escaped)

        return subject, content
