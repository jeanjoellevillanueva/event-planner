"""
Comprehensive timezone tests for Event Planner project.
"""

from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import RequestFactory
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase

from apps.common.mixins import TimezoneAwareMixin
from apps.common.timezone import format_datetime_for_display
from apps.common.timezone import get_current_time_in_timezone
from apps.common.timezone import is_valid_timezone
from apps.common.timezone import to_user_timezone
from apps.common.timezone import to_utc


class TimezoneConversionTests(TestCase):
    """
    Tests for timezone conversion utilities.
    """

    def test_to_user_timezone_converts_utc_to_manila(self):
        """
        UTC datetime should convert correctly to Asia/Manila (+08:00).
        """
        utc_dt = datetime(2026, 8, 10, 6, 0, 0, tzinfo=ZoneInfo('UTC'))
        manila_dt = to_user_timezone(utc_dt, 'Asia/Manila')

        self.assertEqual(manila_dt.hour, 14)
        self.assertEqual(manila_dt.day, 10)
        self.assertEqual(manila_dt.tzinfo, ZoneInfo('Asia/Manila'))

    def test_to_user_timezone_converts_utc_to_new_york(self):
        """
        UTC datetime should convert correctly to America/New_York.
        """
        utc_dt = datetime(2026, 8, 10, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        ny_dt = to_user_timezone(utc_dt, 'America/New_York')

        self.assertEqual(ny_dt.hour, 8)
        self.assertEqual(ny_dt.tzinfo, ZoneInfo('America/New_York'))

    def test_to_user_timezone_handles_none(self):
        """
        None input should return None.
        """
        result = to_user_timezone(None, 'Asia/Manila')
        self.assertIsNone(result)

    def test_to_user_timezone_accepts_zoneinfo_object(self):
        """
        Should accept ZoneInfo object as user_tz parameter.
        """
        utc_dt = datetime(2026, 8, 10, 6, 0, 0, tzinfo=ZoneInfo('UTC'))
        manila_tz = ZoneInfo('Asia/Manila')
        manila_dt = to_user_timezone(utc_dt, manila_tz)

        self.assertEqual(manila_dt.hour, 14)

    def test_to_utc_from_naive_datetime(self):
        """
        Naive datetime with source_tz should convert to UTC.
        """
        naive_dt = datetime(2026, 8, 10, 14, 0, 0)
        utc_dt = to_utc(naive_dt, 'Asia/Manila')

        self.assertEqual(utc_dt.hour, 6)
        self.assertEqual(utc_dt.tzinfo, ZoneInfo('UTC'))

    def test_to_utc_from_aware_datetime(self):
        """
        Already aware datetime should convert to UTC.
        """
        manila_dt = datetime(2026, 8, 10, 14, 0, 0, tzinfo=ZoneInfo('Asia/Manila'))
        utc_dt = to_utc(manila_dt)

        self.assertEqual(utc_dt.hour, 6)
        self.assertEqual(utc_dt.tzinfo, ZoneInfo('UTC'))

    def test_to_utc_handles_none(self):
        """
        None input should return None.
        """
        result = to_utc(None)
        self.assertIsNone(result)

    def test_to_utc_naive_without_source_tz_raises(self):
        """
        Naive datetime without source_tz should raise ValueError.
        """
        naive_dt = datetime(2026, 8, 10, 14, 0, 0)
        with self.assertRaises(ValueError):
            to_utc(naive_dt)

    def test_roundtrip_conversion(self):
        """
        Converting to user timezone and back to UTC should preserve time.
        """
        original_utc = datetime(2026, 8, 10, 6, 0, 0, tzinfo=ZoneInfo('UTC'))
        manila_dt = to_user_timezone(original_utc, 'Asia/Manila')
        back_to_utc = to_utc(manila_dt)

        self.assertEqual(original_utc, back_to_utc)


class TimezoneDSTTests(TestCase):
    """
    Tests for daylight saving time edge cases.
    """

    def test_dst_transition_spring_forward_us_eastern(self):
        """
        US Eastern spring forward: 2:00 AM -> 3:00 AM on March 8, 2026.
        """
        utc_dt = datetime(2026, 3, 8, 7, 0, 0, tzinfo=ZoneInfo('UTC'))
        eastern_dt = to_user_timezone(utc_dt, 'America/New_York')

        self.assertEqual(eastern_dt.hour, 3)
        self.assertEqual(eastern_dt.day, 8)

    def test_dst_transition_fall_back_us_eastern(self):
        """
        US Eastern fall back: 2:00 AM -> 1:00 AM on November 1, 2026.
        """
        utc_before = datetime(2026, 11, 1, 5, 30, 0, tzinfo=ZoneInfo('UTC'))
        utc_after = datetime(2026, 11, 1, 7, 30, 0, tzinfo=ZoneInfo('UTC'))

        eastern_before = to_user_timezone(utc_before, 'America/New_York')
        eastern_after = to_user_timezone(utc_after, 'America/New_York')

        self.assertNotEqual(eastern_before.hour, eastern_after.hour)

    def test_timezone_without_dst(self):
        """
        Asia/Manila has no DST and should work correctly year-round.
        """
        summer_utc = datetime(2026, 7, 15, 6, 0, 0, tzinfo=ZoneInfo('UTC'))
        winter_utc = datetime(2026, 1, 15, 6, 0, 0, tzinfo=ZoneInfo('UTC'))

        summer_manila = to_user_timezone(summer_utc, 'Asia/Manila')
        winter_manila = to_user_timezone(winter_utc, 'Asia/Manila')

        self.assertEqual(summer_manila.hour, 14)
        self.assertEqual(winter_manila.hour, 14)

    def test_dst_ambiguous_time_handling(self):
        """
        During fall back, 1:30 AM occurs twice - should handle gracefully.
        """
        utc_dt = datetime(2026, 11, 1, 6, 30, 0, tzinfo=ZoneInfo('UTC'))
        eastern_dt = to_user_timezone(utc_dt, 'America/New_York')

        self.assertIsNotNone(eastern_dt)
        self.assertEqual(eastern_dt.tzinfo, ZoneInfo('America/New_York'))


class TimezoneValidationTests(TestCase):
    """
    Tests for timezone validation.
    """

    def test_valid_timezone_asia_manila(self):
        """
        Asia/Manila should be a valid timezone.
        """
        self.assertTrue(is_valid_timezone('Asia/Manila'))

    def test_valid_timezone_utc(self):
        """
        UTC should be a valid timezone.
        """
        self.assertTrue(is_valid_timezone('UTC'))

    def test_valid_timezone_america_new_york(self):
        """
        America/New_York should be a valid timezone.
        """
        self.assertTrue(is_valid_timezone('America/New_York'))

    def test_invalid_timezone_rejected(self):
        """
        Invalid timezone name should return False.
        """
        self.assertFalse(is_valid_timezone('Invalid/Zone'))
        self.assertFalse(is_valid_timezone(''))
        self.assertFalse(is_valid_timezone('NotATimezone'))


class TimezoneUtilityTests(TestCase):
    """
    Tests for timezone utility functions.
    """

    def test_get_current_time_in_timezone(self):
        """
        Should return current time in specified timezone.
        """
        manila_now = get_current_time_in_timezone('Asia/Manila')

        self.assertEqual(manila_now.tzinfo, ZoneInfo('Asia/Manila'))

    def test_format_datetime_for_display(self):
        """
        Should format datetime correctly for display.
        """
        utc_dt = datetime(2026, 8, 10, 6, 0, 0, tzinfo=ZoneInfo('UTC'))
        formatted = format_datetime_for_display(utc_dt, 'Asia/Manila', '%Y-%m-%d %H:%M')

        self.assertEqual(formatted, '2026-08-10 14:00')

    def test_format_datetime_handles_none(self):
        """
        Should return None for None input.
        """
        result = format_datetime_for_display(None, 'Asia/Manila')
        self.assertIsNone(result)


class TimezoneSerializerMixinTests(TestCase):
    """
    Tests for TimezoneAwareMixin serializer.
    """

    def create_mock_instance(self):
        """
        Create a mock model instance with datetime fields.
        """
        instance = MagicMock()
        instance.created_at = datetime(2026, 8, 10, 6, 0, 0, tzinfo=ZoneInfo('UTC'))
        instance.updated_at = datetime(2026, 8, 10, 7, 0, 0, tzinfo=ZoneInfo('UTC'))
        instance.name = 'Test'
        return instance

    def test_mixin_converts_datetime_fields(self):
        """
        Mixin should convert all DateTimeField values to user timezone.
        """
        class TestSerializer(TimezoneAwareMixin, serializers.Serializer):
            """
            Test serializer with datetime fields.
            """

            name = serializers.CharField()
            created_at = serializers.DateTimeField()
            updated_at = serializers.DateTimeField()

        factory = APIRequestFactory()
        request = factory.get('/')

        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.timezone = 'Asia/Manila'
        request.user = mock_user

        instance = self.create_mock_instance()
        serializer = TestSerializer(instance, context={'request': request})
        data = serializer.data

        self.assertIn('+08:00', data['created_at'])
        self.assertIn('14:00:00', data['created_at'])

    def test_mixin_preserves_non_datetime_fields(self):
        """
        Mixin should not modify non-datetime fields.
        """
        class TestSerializer(TimezoneAwareMixin, serializers.Serializer):
            """
            Test serializer with mixed fields.
            """

            name = serializers.CharField()
            created_at = serializers.DateTimeField()

        factory = APIRequestFactory()
        request = factory.get('/')

        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.timezone = 'Asia/Manila'
        request.user = mock_user

        instance = self.create_mock_instance()
        serializer = TestSerializer(instance, context={'request': request})
        data = serializer.data

        self.assertEqual(data['name'], 'Test')

    def test_mixin_uses_query_param_timezone(self):
        """
        Mixin should use tz query parameter when provided.
        """
        class TestSerializer(TimezoneAwareMixin, serializers.Serializer):
            """
            Test serializer for timezone override.
            """

            created_at = serializers.DateTimeField()

        factory = APIRequestFactory()
        request = factory.get('/', {'tz': 'America/New_York'})

        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.timezone = 'Asia/Manila'
        request.user = mock_user

        instance = self.create_mock_instance()
        serializer = TestSerializer(instance, context={'request': request})
        data = serializer.data

        self.assertIn('America/New_York', str(to_user_timezone(instance.created_at, 'America/New_York').tzinfo))

    def test_mixin_defaults_to_utc_for_unauthenticated(self):
        """
        Mixin should default to UTC for unauthenticated requests.
        """
        class TestSerializer(TimezoneAwareMixin, serializers.Serializer):
            """
            Test serializer for unauthenticated requests.
            """

            created_at = serializers.DateTimeField()

        factory = APIRequestFactory()
        request = factory.get('/')

        mock_user = MagicMock()
        mock_user.is_authenticated = False
        request.user = mock_user

        instance = self.create_mock_instance()
        serializer = TestSerializer(instance, context={'request': request})
        data = serializer.data

        self.assertIn('+00:00', data['created_at'])


class TimezoneEdgeCaseTests(TestCase):
    """
    Tests for timezone edge cases.
    """

    def test_midnight_boundary_conversion(self):
        """
        Converting midnight UTC should handle date changes correctly.
        """
        utc_midnight = datetime(2026, 8, 10, 0, 0, 0, tzinfo=ZoneInfo('UTC'))
        manila_dt = to_user_timezone(utc_midnight, 'Asia/Manila')

        self.assertEqual(manila_dt.hour, 8)
        self.assertEqual(manila_dt.day, 10)

    def test_end_of_day_boundary_conversion(self):
        """
        Converting 23:59 UTC should handle date changes correctly.
        """
        utc_late = datetime(2026, 8, 10, 23, 59, 59, tzinfo=ZoneInfo('UTC'))
        manila_dt = to_user_timezone(utc_late, 'Asia/Manila')

        self.assertEqual(manila_dt.day, 11)
        self.assertEqual(manila_dt.hour, 7)

    def test_year_boundary_conversion(self):
        """
        Converting across year boundary should work correctly.
        """
        utc_nye = datetime(2026, 12, 31, 20, 0, 0, tzinfo=ZoneInfo('UTC'))
        manila_dt = to_user_timezone(utc_nye, 'Asia/Manila')

        self.assertEqual(manila_dt.year, 2027)
        self.assertEqual(manila_dt.month, 1)
        self.assertEqual(manila_dt.day, 1)
        self.assertEqual(manila_dt.hour, 4)

    def test_leap_year_february_29(self):
        """
        Leap year February 29 should convert correctly.
        """
        utc_leap = datetime(2028, 2, 29, 6, 0, 0, tzinfo=ZoneInfo('UTC'))
        manila_dt = to_user_timezone(utc_leap, 'Asia/Manila')

        self.assertEqual(manila_dt.month, 2)
        self.assertEqual(manila_dt.day, 29)
        self.assertEqual(manila_dt.hour, 14)

    def test_negative_utc_offset_timezone(self):
        """
        Timezones with negative UTC offset should work correctly.
        """
        utc_dt = datetime(2026, 8, 10, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        la_dt = to_user_timezone(utc_dt, 'America/Los_Angeles')

        self.assertEqual(la_dt.hour, 5)
        self.assertEqual(la_dt.day, 10)

    def test_half_hour_offset_timezone(self):
        """
        Timezones with half-hour offsets should work correctly (e.g., India).
        """
        utc_dt = datetime(2026, 8, 10, 12, 0, 0, tzinfo=ZoneInfo('UTC'))
        india_dt = to_user_timezone(utc_dt, 'Asia/Kolkata')

        self.assertEqual(india_dt.hour, 17)
        self.assertEqual(india_dt.minute, 30)


class TimezoneStorageTests(TestCase):
    """
    Tests for UTC storage of datetime fields.
    """

    def test_datetime_stored_with_utc_tzinfo(self):
        """
        Datetime should be stored with UTC timezone info.
        """
        input_dt = datetime(2026, 8, 10, 14, 0, 0, tzinfo=ZoneInfo('Asia/Manila'))
        stored_dt = to_utc(input_dt)

        self.assertEqual(stored_dt.tzinfo, ZoneInfo('UTC'))

    def test_utc_storage_preserves_instant(self):
        """
        UTC storage should preserve the exact instant in time.
        """
        manila_dt = datetime(2026, 8, 10, 14, 0, 0, tzinfo=ZoneInfo('Asia/Manila'))
        utc_dt = to_utc(manila_dt)

        self.assertEqual(
            manila_dt.timestamp(),
            utc_dt.timestamp()
        )
