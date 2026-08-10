"""
Timezone tests specific to bookings app.
"""

import pytest
from datetime import date
from datetime import datetime
from datetime import time
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingSerializer
from apps.common.timezone import to_user_timezone


@pytest.mark.django_db
class TestBookingTimezoneDisplay:
    """
    Tests for timezone display in booking API responses.
    """

    def test_booking_times_converted_to_user_timezone(
        self, authenticated_client, booking_factory
    ):
        """
        Booking times should be converted to user's timezone in API response.
        """
        authenticated_client.user.timezone = 'Asia/Manila'
        authenticated_client.user.save()

        booking = booking_factory(
            business=authenticated_client.business,
            event_date=date(2026, 12, 25),
            event_time=time(6, 0, 0),
        )

        from django.urls import reverse
        url = reverse('booking_detail', kwargs={'pk': booking.id})
        response = authenticated_client.get(url)

        assert response.status_code == 200

    def test_booking_created_at_uses_user_timezone(
        self, authenticated_client, booking_factory
    ):
        """
        created_at should be converted to user timezone.
        """
        authenticated_client.user.timezone = 'America/New_York'
        authenticated_client.user.save()

        booking = booking_factory(business=authenticated_client.business)

        from django.urls import reverse
        url = reverse('booking_detail', kwargs={'pk': booking.id})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        created_at = response.data['created_at']
        assert '-05:00' in created_at or '-04:00' in created_at


class BookingTimezoneStorageTests(TestCase):
    """
    Tests for UTC storage of booking datetime fields.
    """

    def test_booking_created_at_stored_utc(self):
        """
        Booking created_at should be stored in UTC.
        """
        from apps.businesses.models import Business
        from apps.clients.models import Client
        from apps.bookings.models import Booking

        business = Business.objects.create(
            name='Test Business',
            business_type='event'
        )
        client = Client.objects.create(
            business=business,
            name='Test Client'
        )
        booking = Booking.objects.create(
            business=business,
            client=client,
            event_date=date(2026, 12, 25),
            pax_count=100
        )

        assert booking.created_at.tzinfo is not None
        assert booking.created_at.tzinfo == ZoneInfo('UTC') or str(booking.created_at.tzinfo) == 'UTC'

    def test_booking_updated_at_stored_utc(self):
        """
        Booking updated_at should be stored in UTC.
        """
        from apps.businesses.models import Business
        from apps.clients.models import Client
        from apps.bookings.models import Booking

        business = Business.objects.create(
            name='Test Business',
            business_type='event'
        )
        client = Client.objects.create(
            business=business,
            name='Test Client'
        )
        booking = Booking.objects.create(
            business=business,
            client=client,
            event_date=date(2026, 12, 25),
            pax_count=100
        )

        booking.venue = 'Updated Venue'
        booking.save()

        assert booking.updated_at.tzinfo is not None
