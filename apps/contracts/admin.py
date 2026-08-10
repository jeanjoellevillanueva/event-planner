"""
Admin configuration for contracts app.
"""

from django.contrib import admin

from apps.contracts.models import Contract
from apps.contracts.models import ContractTemplate


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    """
    Admin configuration for ContractTemplate model.
    """

    list_display = ['name', 'business', 'is_default', 'is_active', 'created_at']
    list_filter = ['business', 'is_default', 'is_active']
    search_fields = ['name', 'description']
    raw_id_fields = ['business']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """
    Admin configuration for Contract model.
    """

    list_display = ['id', 'booking', 'template', 'status', 'signed_at', 'created_at']
    list_filter = ['status', 'signed_at']
    search_fields = ['booking__client__name', 'signed_by']
    raw_id_fields = ['booking', 'template', 'generated_by']
    readonly_fields = ['created_at', 'updated_at']
