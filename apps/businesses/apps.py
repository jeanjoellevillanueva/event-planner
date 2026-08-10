"""
App configuration for businesses app.
"""

from django.apps import AppConfig


class BusinessesConfig(AppConfig):
    """
    Configuration for businesses app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.businesses'
