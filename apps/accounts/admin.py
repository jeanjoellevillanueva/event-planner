"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import BusinessMembership
from apps.accounts.models import Invitation
from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for User model.
    """

    list_display = ['email', 'username', 'timezone', 'current_business', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_staff', 'timezone']
    search_fields = ['email', 'username']
    ordering = ['-created_at']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'timezone', 'current_business')}),
    )


@admin.register(BusinessMembership)
class BusinessMembershipAdmin(admin.ModelAdmin):
    """
    Admin configuration for BusinessMembership model.
    """

    list_display = ['user', 'business', 'role', 'created_at']
    list_filter = ['role']
    search_fields = ['user__email', 'business__name']
    raw_id_fields = ['user', 'business']


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Invitation model.
    """

    list_display = ['email', 'business', 'role', 'status', 'invited_by', 'expires_at']
    list_filter = ['status', 'role']
    search_fields = ['email', 'business__name']
    raw_id_fields = ['business', 'invited_by']
    readonly_fields = ['token', 'created_at']
