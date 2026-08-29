"""
App configuration for the Tailwind web UI.
"""

from django.apps import AppConfig


class WebConfig(AppConfig):
    """
    Configuration for the session-auth web UI.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.web'
