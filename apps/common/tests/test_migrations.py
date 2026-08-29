"""
Tests that Django migrations exist and match models.
"""

from io import StringIO
from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase


class MigrationFilesTests(TestCase):
    """
    Tests for committed app migrations.
    """

    PROJECT_APPS = (
        'accounts',
        'businesses',
        'clients',
        'products',
        'bookings',
        'contracts',
        'teams',
        'reminders',
    )

    def test_each_project_app_has_initial_migration(self):
        """
        Every project app with models should ship an initial migration.
        """
        workspace = Path(__file__).resolve().parents[3]
        for app_label in self.PROJECT_APPS:
            migration = workspace / 'apps' / app_label / 'migrations' / '0001_initial.py'
            self.assertTrue(migration.exists(), f'Missing {migration}')

    def test_migration_graph_is_consistent(self):
        """
        Migration loader should build a consistent graph.
        """
        loader = MigrationLoader(None, ignore_no_migrations=True)
        conflicts = loader.detect_conflicts()
        self.assertEqual(conflicts, {})

    def test_models_have_no_unapplied_migration_changes(self):
        """
        Models should not require new migrations.
        """
        output = StringIO()
        try:
            call_command(
                'makemigrations',
                *self.PROJECT_APPS,
                check=True,
                dry_run=True,
                verbosity=0,
                stdout=output,
                stderr=output,
            )
        except SystemExit as exc:
            self.assertEqual(exc.code, 0, output.getvalue())
        except CommandError as exc:
            self.fail(str(exc))

    def test_project_apps_are_installed(self):
        """
        Project apps used by migrations should be installed.
        """
        for app_label in self.PROJECT_APPS:
            self.assertTrue(apps.is_installed(f'apps.{app_label}'))

    def test_postgres_sql_includes_positive_integer_checks(self):
        """
        Hand-written Postgres SQL should match Django PositiveIntegerField checks.
        """
        workspace = Path(__file__).resolve().parents[3]
        sql = (workspace / 'sql' / '0001_app_tables.postgresql.sql').read_text()
        for column in ('min_pax', 'max_pax', 'quantity', 'pax_count', 'retry_count'):
            self.assertIn(f'CHECK ({column} >= 0)', sql)
