"""
Client models for Event Planner project.
"""

from django.db import models

from apps.common.models import BusinessScopedModel


class Client(BusinessScopedModel):
    """
    Client model representing a customer of a business.
    """

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    secondary_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.business.name})"

    def get_booking_count(self):
        """
        Get total number of bookings for this client.
        """
        return self.bookings.count()

    def get_total_spent(self):
        """
        Get total amount spent by this client.
        """
        from django.db.models import Sum
        total = self.bookings.filter(
            status__in=['confirmed', 'completed']
        ).aggregate(total=Sum('total_amount'))
        return total['total'] or 0
