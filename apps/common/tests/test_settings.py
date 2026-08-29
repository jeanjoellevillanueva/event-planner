"""
Tests for documented project settings.
"""

from pathlib import Path

from django.conf import settings
from django.test import TestCase


class FrontendSettingsTests(TestCase):
    """
    Tests that web UI settings match the README.
    """

    def test_frontend_url_defaults_to_django_web_ui(self):
        """
        Invite links should point at the Django UI, not a separate :3000 app.
        """
        self.assertEqual(settings.FRONTEND_URL, 'http://localhost:8000')

    def test_readme_documents_production_migrate(self):
        """
        Production docs should tell operators to apply migrations themselves.
        """
        readme = (Path(__file__).resolve().parents[3] / 'README.md').read_text()
        self.assertIn('docker-compose.prod.yml', readme)
        self.assertIn('manage.py migrate', readme)

    def test_login_urls_are_configured_for_upcoming_web_pages(self):
        """
        Session login settings should match the planned Tailwind routes.
        """
        self.assertEqual(settings.LOGIN_URL, '/login/')
        self.assertEqual(settings.LOGIN_REDIRECT_URL, '/dashboard/')
        self.assertEqual(settings.LOGOUT_REDIRECT_URL, '/login/')
