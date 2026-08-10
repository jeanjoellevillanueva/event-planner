"""
Admin configuration for clients app.
"""

from django.contrib import admin

from apps.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Admin configuration for Client model.
    """

    list_display = ['name', 'business', 'email', 'phone', 'city', 'is_active', 'created_at']
    list_filter = ['business', 'is_active', 'city']
    search_fields = ['name', 'email', 'phone']
    raw_id_fields = ['business']
    readonly_fields = ['created_at', 'updated_at']
