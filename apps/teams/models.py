"""
Team models for Event Planner project.
"""

from django.conf import settings
from django.db import models

from apps.common.models import BusinessScopedModel


class TeamMember(BusinessScopedModel):
    """
    Team member model (can be linked to user or standalone).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_profiles',
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=100, help_text="e.g., Coordinator, Photographer, Chef")
    availability = models.JSONField(
        default=dict,
        blank=True,
        help_text="Availability schedule by day of week"
    )
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.role} ({self.business.name})"

    def get_assigned_bookings(self, from_date=None, to_date=None):
        """
        Get bookings assigned to this team member.
        """
        assignments = self.booking_assignments.select_related('booking')

        if from_date:
            assignments = assignments.filter(booking__event_date__gte=from_date)
        if to_date:
            assignments = assignments.filter(booking__event_date__lte=to_date)

        return [a.booking for a in assignments]


class BookingAssignment(models.Model):
    """
    Assignment of team member to a booking.
    """

    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='team_assignments',
    )
    team_member = models.ForeignKey(
        TeamMember,
        on_delete=models.CASCADE,
        related_name='booking_assignments',
    )
    role = models.CharField(max_length=100, blank=True, help_text="Role for this specific event")
    notes = models.TextField(blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='made_assignments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['booking', 'team_member']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.team_member.name} assigned to Booking #{self.booking.id}"
