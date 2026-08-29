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
        self.assertEqual(settings.FRONTEND_URL, 'http://localhost:6000')

    def test_readme_documents_production_migrate(self):
        """
        Production docs should tell operators to apply migrations themselves.
        """
        readme = (Path(__file__).resolve().parents[3] / 'README.md').read_text()
        self.assertIn('docker-compose.prod.yml', readme)
        self.assertIn('manage.py migrate', readme)

    def test_celery_beat_schedules_reminder_tasks(self):
        """
        Beat should process due reminders and create event reminders.
        """
        names = set(settings.CELERY_BEAT_SCHEDULE)
        self.assertIn('process-pending-reminders', names)
        self.assertIn('create-event-reminders', names)

    def test_dev_compose_uses_isolated_ports_and_database(self):
        """
        Local Docker should not bind the default 8000/5432/6379 ports.
        """
        compose = (Path(__file__).resolve().parents[3] / 'docker-compose.yml').read_text()
        self.assertIn('name: event-planner', compose)
        self.assertIn('"6000:8000"', compose)
        self.assertIn('"6543:5432"', compose)
        self.assertIn('"6380:6379"', compose)
        self.assertIn('POSTGRES_DB: event_planner', compose)
        self.assertIn('event_planner_pgdata', compose)
        self.assertNotIn('"8000:8000"', compose)
        self.assertNotIn('"5432:5432"', compose)
        self.assertNotIn('"6379:6379"', compose)

    def test_login_urls_point_at_web_pages(self):
        """
        Session login should use the Tailwind login page.
        """
        self.assertEqual(settings.LOGIN_URL, '/login/')
        self.assertEqual(settings.LOGIN_REDIRECT_URL, '/dashboard/')
        self.assertEqual(settings.LOGOUT_REDIRECT_URL, '/login/')
