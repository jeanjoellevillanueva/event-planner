"""
App configuration for contracts app.
"""

from django.apps import AppConfig


class ContractsConfig(AppConfig):
    """
    Configuration for contracts app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contracts'
