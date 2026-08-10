"""
App configuration for bookings app.
"""

from django.apps import AppConfig


class BookingsConfig(AppConfig):
    """
    Configuration for bookings app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bookings'
