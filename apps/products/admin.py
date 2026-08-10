"""
Admin configuration for products app.
"""

from django.contrib import admin

from apps.products.models import Package
from apps.products.models import PackageItem
from apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for Product model.
    """

    list_display = ['name', 'business', 'category', 'base_price', 'is_active', 'created_at']
    list_filter = ['business', 'category', 'is_active']
    search_fields = ['name', 'description']
    raw_id_fields = ['business']
    readonly_fields = ['created_at', 'updated_at']


class PackageItemInline(admin.TabularInline):
    """
    Inline admin for PackageItem.
    """

    model = PackageItem
    extra = 1
    raw_id_fields = ['product']


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """
    Admin configuration for Package model.
    """

    list_display = ['name', 'business', 'base_price', 'min_pax', 'max_pax', 'is_active', 'created_at']
    list_filter = ['business', 'is_active']
    search_fields = ['name', 'description']
    raw_id_fields = ['business']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PackageItemInline]
