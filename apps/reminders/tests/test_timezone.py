"""
Timezone tests for reminders app.
"""

import pytest
from datetime import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone

from apps.common.timezone import to_user_timezone
from apps.common.timezone import to_utc


class ReminderTimezoneTests(TestCase):
    """
    Tests for reminder scheduling across timezones.
    """

    def test_schedule_reminder_in_user_timezone(self):
        """
        Reminder scheduled in user's timezone should be stored in UTC.
        """
        manila_time = datetime(2026, 8, 10, 14, 0, 0, tzinfo=ZoneInfo('Asia/Manila'))
        utc_time = to_utc(manila_time)

        self.assertEqual(utc_time.hour, 6)
        self.assertEqual(utc_time.tzinfo, ZoneInfo('UTC'))

    def test_reminder_scheduled_at_preserves_instant(self):
        """
        Converting scheduled_at should preserve the exact moment.
        """
        manila_time = datetime(2026, 8, 10, 14, 0, 0, tzinfo=ZoneInfo('Asia/Manila'))
        utc_time = to_utc(manila_time)
        back_to_manila = to_user_timezone(utc_time, 'Asia/Manila')

        self.assertEqual(manila_time, back_to_manila)

    def test_reminder_across_date_boundary(self):
        """
        Reminder scheduled near midnight should handle date boundary.
        """
        late_manila = datetime(2026, 8, 10, 23, 0, 0, tzinfo=ZoneInfo('Asia/Manila'))
        utc_time = to_utc(late_manila)

        self.assertEqual(utc_time.hour, 15)
        self.assertEqual(utc_time.day, 10)

    def test_reminder_scheduled_for_dst_timezone(self):
        """
        Reminder in DST timezone should handle transitions.
        """
        eastern_summer = datetime(2026, 7, 4, 9, 0, 0, tzinfo=ZoneInfo('America/New_York'))
        utc_time = to_utc(eastern_summer)

        self.assertEqual(utc_time.hour, 13)

        eastern_winter = datetime(2026, 1, 15, 9, 0, 0, tzinfo=ZoneInfo('America/New_York'))
        utc_winter = to_utc(eastern_winter)

        self.assertEqual(utc_winter.hour, 14)


@pytest.mark.django_db
class TestReminderAPITimezone:
    """
    Tests for reminder API timezone handling.
    """

    def test_reminder_list_uses_user_timezone(self, authenticated_client, booking_factory):
        """
        Reminder listing should convert times to user timezone.
        """
        from apps.reminders.models import Reminder
        from django.urls import reverse

        authenticated_client.user.timezone = 'Asia/Manila'
        authenticated_client.user.save()

        booking = booking_factory(business=authenticated_client.business)

        Reminder.objects.create(
            booking=booking,
            reminder_type='email',
            scheduled_at=timezone.now() + timedelta(days=1),
            message='Test reminder',
            recipient_email='test@example.com'
        )

        url = reverse('reminder_list_create')
        response = authenticated_client.get(url)

        assert response.status_code == 200

        results = response.data.get('results', response.data)
        if results:
            scheduled_at = results[0]['scheduled_at']
            assert '+08:00' in scheduled_at
