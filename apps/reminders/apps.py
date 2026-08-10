"""
App configuration for reminders app.
"""

from django.apps import AppConfig


class RemindersConfig(AppConfig):
    """
    Configuration for reminders app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reminders'
