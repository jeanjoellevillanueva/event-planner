"""
Tests for Twilio SMS reminder sending.
"""

from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.reminders.models import Reminder
from apps.reminders.sms import send_sms_reminder
from apps.reminders.sms import twilio_is_configured
from apps.reminders.tasks import send_reminder


@pytest.mark.django_db
class TestTwilioSms:
    """
    Tests for Twilio configuration and sending.
    """

    def test_twilio_is_not_configured_by_default(self):
        """
        Empty Twilio settings should report unconfigured.
        """
        assert twilio_is_configured() is False

    def test_send_sms_returns_false_when_unconfigured(self, booking_factory):
        """
        Missing Twilio credentials should skip sending.
        """
        reminder = Reminder.objects.create(
            booking=booking_factory(),
            reminder_type='sms',
            scheduled_at=timezone.now(),
            message='Hello',
            recipient_phone='+15555550100',
        )
        assert send_sms_reminder(reminder) is False

    @override_settings(
        TWILIO_ACCOUNT_SID='sid',
        TWILIO_AUTH_TOKEN='token',
        TWILIO_FROM_NUMBER='+15555550199',
    )
    @patch('apps.reminders.sms.get_twilio_client')
    def test_send_sms_uses_twilio_when_configured(self, mock_get_client, booking_factory):
        """
        Configured Twilio should send the reminder body to the recipient.
        """
        messages = MagicMock()
        mock_get_client.return_value.messages = messages
        reminder = Reminder.objects.create(
            booking=booking_factory(),
            reminder_type='sms',
            scheduled_at=timezone.now(),
            message='Event tomorrow',
            recipient_phone='+15555550100',
        )

        assert send_sms_reminder(reminder) is True
        messages.create.assert_called_once_with(
            body='Event tomorrow',
            from_='+15555550199',
            to='+15555550100',
        )

    def test_send_reminder_task_marks_sms_failed_when_unconfigured(self, booking_factory):
        """
        The Celery task should mark SMS failed when Twilio is unset.
        """
        reminder = Reminder.objects.create(
            booking=booking_factory(),
            reminder_type='sms',
            scheduled_at=timezone.now() - timedelta(minutes=1),
            message='Hello',
            recipient_phone='+15555550100',
        )

        result = send_reminder(reminder.id)
        reminder.refresh_from_db()
        assert 'SMS not configured' in result
        assert reminder.status == 'failed'

    @override_settings(
        TWILIO_ACCOUNT_SID='sid',
        TWILIO_AUTH_TOKEN='token',
        TWILIO_FROM_NUMBER='+15555550199',
    )
    @patch('apps.reminders.tasks.send_sms_reminder', side_effect=Exception('twilio down'))
    def test_sms_exception_stays_pending_for_retry(self, mock_send, booking_factory):
        """
        Transient Twilio errors should keep the reminder pending so retries can send.
        """
        reminder = Reminder.objects.create(
            booking=booking_factory(),
            reminder_type='sms',
            scheduled_at=timezone.now() - timedelta(minutes=1),
            message='Hello',
            recipient_phone='+15555550100',
        )

        with pytest.raises(Exception, match='twilio down'):
            send_reminder.run(reminder.id)

        reminder.refresh_from_db()
        assert reminder.status == 'pending'
        assert reminder.retry_count == 1
        assert reminder.error_message == 'twilio down'
