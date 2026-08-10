"""
Admin configuration for teams app.
"""

from django.contrib import admin

from apps.teams.models import BookingAssignment
from apps.teams.models import TeamMember


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """
    Admin configuration for TeamMember model.
    """

    list_display = ['name', 'business', 'role', 'user', 'is_active', 'created_at']
    list_filter = ['business', 'role', 'is_active']
    search_fields = ['name', 'email', 'role']
    raw_id_fields = ['business', 'user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BookingAssignment)
class BookingAssignmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for BookingAssignment model.
    """

    list_display = ['booking', 'team_member', 'role', 'assigned_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['team_member__name', 'booking__client__name']
    raw_id_fields = ['booking', 'team_member', 'assigned_by']
    readonly_fields = ['created_at']
