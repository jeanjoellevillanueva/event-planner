"""
Contract models for Event Planner project.
"""

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.common.models import BusinessScopedModel


class ContractTemplate(BusinessScopedModel):
    """
    Template for generating contracts.
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content = models.TextField(help_text="HTML template content with placeholders")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def save(self, *args, **kwargs):
        if self.is_default:
            ContractTemplate.objects.filter(
                business=self.business,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Contract(BaseModel):
    """
    Generated contract for a booking.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('sent', 'Sent'),
        ('signed', 'Signed'),
        ('cancelled', 'Cancelled'),
    ]

    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='contracts',
    )
    template = models.ForeignKey(
        ContractTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contracts',
    )
    rendered_content = models.TextField(blank=True)
    generated_file = models.FileField(upload_to='contracts/', null=True, blank=True)
    signed_file = models.FileField(upload_to='contracts/signed/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.CharField(max_length=200, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_contracts',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Contract for Booking #{self.booking.id}"

    def render_content(self):
        """
        Render template with booking data.
        """
        if not self.template:
            return ''

        booking = self.booking
        client = booking.client
        business = booking.business
        package = booking.package

        context = {
            'business_name': business.name,
            'business_address': business.address,
            'business_email': business.email,
            'business_phone': business.phone,
            'client_name': client.name,
            'client_email': client.email,
            'client_phone': client.phone,
            'client_address': client.address,
            'event_date': booking.event_date.strftime('%B %d, %Y'),
            'event_time': booking.event_time.strftime('%I:%M %p') if booking.event_time else '',
            'venue': booking.venue,
            'venue_address': booking.venue_address,
            'pax_count': booking.pax_count,
            'package_name': package.name if package else 'Custom Package',
            'total_amount': f"{booking.total_amount:,.2f}",
            'deposit_amount': f"{booking.deposit_amount:,.2f}",
            'balance_amount': f"{booking.balance_amount:,.2f}",
            'special_requests': booking.special_requests,
            'notes': booking.notes,
        }

        content = self.template.content
        for key, value in context.items():
            content = content.replace(f'{{{{{key}}}}}', str(value))

        self.rendered_content = content
        return content
