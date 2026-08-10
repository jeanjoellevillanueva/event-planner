"""
Admin configuration for businesses app.
"""

from django.contrib import admin

from apps.businesses.models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """
    Admin configuration for Business model.
    """

    list_display = ['name', 'business_type', 'email', 'is_active', 'created_at']
    list_filter = ['business_type', 'is_active']
    search_fields = ['name', 'email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
