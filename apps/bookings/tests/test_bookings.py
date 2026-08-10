"""
Tests for bookings app.
"""

import pytest
from datetime import date
from datetime import time
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestBookingCreation:
    """
    Tests for booking creation.
    """

    def test_create_booking_success(self, authenticated_client, client_factory, package_factory):
        """
        Should create booking with valid data.
        """
        client = client_factory(business=authenticated_client.business)
        package = package_factory(business=authenticated_client.business)

        url = reverse('booking_list_create')
        data = {
            'client': client.id,
            'package': package.id,
            'event_date': '2026-12-25',
            'event_time': '14:00:00',
            'venue': 'Grand Ballroom',
            'pax_count': 100,
            'total_amount': '15000.00',
            'deposit_amount': '5000.00',
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['venue'] == 'Grand Ballroom'
        assert response.data['pax_count'] == 100

    def test_create_booking_invalid_client(self, authenticated_client, business_factory, client_factory):
        """
        Should reject booking with client from different business.
        """
        other_business = business_factory(name='Other Business')
        other_client = client_factory(business=other_business)

        url = reverse('booking_list_create')
        data = {
            'client': other_client.id,
            'event_date': '2026-12-25',
            'venue': 'Grand Ballroom',
            'pax_count': 100,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_booking_exceeds_max_pax(self, authenticated_client, client_factory, package_factory):
        """
        Should reject booking exceeding package max pax.
        """
        client = client_factory(business=authenticated_client.business)
        package = package_factory(business=authenticated_client.business, max_pax=100)

        url = reverse('booking_list_create')
        data = {
            'client': client.id,
            'package': package.id,
            'event_date': '2026-12-25',
            'pax_count': 150,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'pax_count' in response.data


@pytest.mark.django_db
class TestBookingReschedule:
    """
    Tests for booking reschedule functionality.
    """

    def test_reschedule_booking_success(self, authenticated_client, booking_factory):
        """
        Should reschedule a pending/confirmed booking.
        """
        booking = booking_factory(
            business=authenticated_client.business,
            status='confirmed'
        )

        url = reverse('booking_reschedule', kwargs={'pk': booking.id})
        data = {
            'new_date': '2026-12-31',
            'reason': 'Client requested change',
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        booking.refresh_from_db()
        assert booking.event_date == date(2026, 12, 31)
        assert booking.reschedules.count() == 1

    def test_reschedule_completed_booking_fails(self, authenticated_client, booking_factory):
        """
        Should reject reschedule for completed booking.
        """
        booking = booking_factory(
            business=authenticated_client.business,
            status='completed'
        )

        url = reverse('booking_reschedule', kwargs={'pk': booking.id})
        data = {'new_date': '2026-12-31'}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reschedule_cancelled_booking_fails(self, authenticated_client, booking_factory):
        """
        Should reject reschedule for cancelled booking.
        """
        booking = booking_factory(
            business=authenticated_client.business,
            status='cancelled'
        )

        url = reverse('booking_reschedule', kwargs={'pk': booking.id})
        data = {'new_date': '2026-12-31'}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBookingCalendar:
    """
    Tests for booking calendar endpoint.
    """

    def test_calendar_returns_events(self, authenticated_client, booking_factory):
        """
        Should return bookings as calendar events.
        """
        booking_factory(
            business=authenticated_client.business,
            event_date=date(2026, 12, 25)
        )

        url = reverse('booking_calendar')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert 'title' in response.data[0]
        assert 'start' in response.data[0]
        assert 'color' in response.data[0]

    def test_calendar_timezone_override(self, authenticated_client, booking_factory):
        """
        Should apply timezone override from query param.
        """
        booking_factory(
            business=authenticated_client.business,
            event_date=date(2026, 12, 25)
        )

        url = reverse('booking_calendar') + '?tz=America/New_York'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_calendar_invalid_timezone_rejected(self, authenticated_client):
        """
        Should reject invalid timezone parameter.
        """
        url = reverse('booking_calendar') + '?tz=Invalid/Zone'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_calendar_date_filter(self, authenticated_client, booking_factory):
        """
        Should filter calendar by date range.
        """
        booking_factory(
            business=authenticated_client.business,
            event_date=date(2026, 12, 25)
        )
        booking_factory(
            business=authenticated_client.business,
            event_date=date(2027, 1, 15)
        )

        url = reverse('booking_calendar') + '?start=2026-12-01&end=2026-12-31'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
