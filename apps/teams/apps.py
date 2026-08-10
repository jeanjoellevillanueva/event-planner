"""
App configuration for teams app.
"""

from django.apps import AppConfig


class TeamsConfig(AppConfig):
    """
    Configuration for teams app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.teams'
