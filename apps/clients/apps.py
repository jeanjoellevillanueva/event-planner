"""
App configuration for clients app.
"""

from django.apps import AppConfig


class ClientsConfig(AppConfig):
    """
    Configuration for clients app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clients'
