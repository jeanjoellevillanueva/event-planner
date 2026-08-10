"""
Booking models for Event Planner project.
"""

from django.conf import settings
from django.db import models

from apps.common.models import BusinessScopedModel


class Booking(BusinessScopedModel):
    """
    Booking model representing an event reservation.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    package = models.ForeignKey(
        'products.Package',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
    )
    event_date = models.DateField()
    event_time = models.TimeField(null=True, blank=True)
    event_end_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=500, blank=True)
    venue_address = models.TextField(blank=True)
    pax_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    special_requests = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bookings',
    )

    class Meta:
        ordering = ['-event_date', '-created_at']

    def __str__(self):
        return f"Booking #{self.id} - {self.client.name} on {self.event_date}"

    def save(self, *args, **kwargs):
        self.balance_amount = self.total_amount - self.deposit_amount
        super().save(*args, **kwargs)

    def can_reschedule(self):
        """
        Check if booking can be rescheduled.
        """
        return self.status in ['pending', 'confirmed']

    def reschedule(self, new_date, new_time=None, reason='', approved_by=None):
        """
        Reschedule booking to a new date.
        """
        if not self.can_reschedule():
            raise ValueError("Cannot reschedule a completed or cancelled booking")

        old_date = self.event_date
        old_time = self.event_time

        BookingReschedule.objects.create(
            booking=self,
            old_date=old_date,
            old_time=old_time,
            new_date=new_date,
            new_time=new_time or old_time,
            reason=reason,
            approved_by=approved_by
        )

        self.event_date = new_date
        if new_time:
            self.event_time = new_time
        self.save(update_fields=['event_date', 'event_time', 'updated_at'])


class BookingReschedule(models.Model):
    """
    Audit trail for booking reschedules.
    """

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='reschedules',
    )
    old_date = models.DateField()
    old_time = models.TimeField(null=True, blank=True)
    new_date = models.DateField()
    new_time = models.TimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_reschedules',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reschedule: {self.old_date} -> {self.new_date}"
