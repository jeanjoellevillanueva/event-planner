"""
Admin configuration for reminders app.
"""

from django.contrib import admin

from apps.reminders.models import Reminder
from apps.reminders.models import ReminderTemplate


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Reminder model.
    """

    list_display = ['id', 'booking', 'reminder_type', 'status', 'scheduled_at', 'sent_at']
    list_filter = ['status', 'reminder_type', 'scheduled_at']
    search_fields = ['booking__client__name', 'subject', 'message']
    raw_id_fields = ['booking']
    readonly_fields = ['sent_at', 'created_at', 'updated_at']


@admin.register(ReminderTemplate)
class ReminderTemplateAdmin(admin.ModelAdmin):
    """
    Admin configuration for ReminderTemplate model.
    """

    list_display = ['name', 'business', 'template_type', 'is_active', 'created_at']
    list_filter = ['business', 'template_type', 'is_active']
    search_fields = ['name', 'subject', 'content']
    raw_id_fields = ['business']
    readonly_fields = ['created_at', 'updated_at']
