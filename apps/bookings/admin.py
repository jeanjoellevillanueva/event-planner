"""
Admin configuration for bookings app.
"""

from django.contrib import admin

from apps.bookings.models import Booking
from apps.bookings.models import BookingReschedule


class BookingRescheduleInline(admin.TabularInline):
    """
    Inline admin for BookingReschedule.
    """

    model = BookingReschedule
    extra = 0
    readonly_fields = ['old_date', 'old_time', 'new_date', 'new_time', 'reason', 'approved_by', 'created_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Admin configuration for Booking model.
    """

    list_display = [
        'id', 'client', 'business', 'event_date', 'event_time',
        'status', 'total_amount', 'created_at'
    ]
    list_filter = ['business', 'status', 'event_date']
    search_fields = ['client__name', 'venue', 'notes']
    raw_id_fields = ['business', 'client', 'package', 'created_by']
    readonly_fields = ['balance_amount', 'created_at', 'updated_at']
    inlines = [BookingRescheduleInline]
    date_hierarchy = 'event_date'


@admin.register(BookingReschedule)
class BookingRescheduleAdmin(admin.ModelAdmin):
    """
    Admin configuration for BookingReschedule model.
    """

    list_display = ['booking', 'old_date', 'new_date', 'approved_by', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['booking', 'approved_by']
    readonly_fields = ['created_at']
