"""
App configuration for products app.
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """
    Configuration for products app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
