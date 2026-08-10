"""
Tests for bookings serializers.
"""

import pytest
from datetime import date
from datetime import time
from rest_framework.test import APIRequestFactory

from apps.bookings.models import Booking
from apps.bookings.serializers import BookingCreateSerializer
from apps.bookings.serializers import BookingListSerializer
from apps.bookings.serializers import BookingRescheduleRequestSerializer
from apps.bookings.serializers import BookingSerializer


@pytest.mark.django_db
class TestBookingSerializer:
    """
    Tests for BookingSerializer.
    """

    def test_serialize_booking(self, booking_factory):
        """
        Should serialize booking with related names.
        """
        booking = booking_factory()

        serializer = BookingSerializer(booking)
        data = serializer.data

        assert 'client_name' in data
        assert 'package_name' in data
        assert 'event_date' in data
        assert 'reschedules' in data

    def test_balance_amount_computed(self, booking_factory):
        """
        Should compute balance correctly.
        """
        booking = booking_factory(total_amount=10000, deposit_amount=3000)

        serializer = BookingSerializer(booking)
        assert serializer.data['balance_amount'] == '7000.00'


@pytest.mark.django_db
class TestBookingCreateSerializer:
    """
    Tests for BookingCreateSerializer.
    """

    def test_valid_booking_creation(self, authenticated_client, client_factory, package_factory):
        """
        Should validate correct booking data.
        """
        client = client_factory(business=authenticated_client.business)
        package = package_factory(business=authenticated_client.business, min_pax=50, max_pax=200)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'client': client.id,
            'package': package.id,
            'event_date': '2026-12-25',
            'event_time': '14:00:00',
            'venue': 'Grand Ballroom',
            'pax_count': 100,
            'total_amount': '15000.00',
        }
        serializer = BookingCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_client_from_other_business_rejected(self, authenticated_client, business_factory, client_factory):
        """
        Should reject client from different business.
        """
        other_business = business_factory(name='Other Business')
        other_client = client_factory(business=other_business)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'client': other_client.id,
            'event_date': '2026-12-25',
            'pax_count': 100,
        }
        serializer = BookingCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'client' in serializer.errors

    def test_package_from_other_business_rejected(self, authenticated_client, business_factory, client_factory, package_factory):
        """
        Should reject package from different business.
        """
        other_business = business_factory(name='Other Business')
        other_package = package_factory(business=other_business)
        client = client_factory(business=authenticated_client.business)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'client': client.id,
            'package': other_package.id,
            'event_date': '2026-12-25',
            'pax_count': 100,
        }
        serializer = BookingCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'package' in serializer.errors

    def test_pax_exceeds_package_max(self, authenticated_client, client_factory, package_factory):
        """
        Should reject pax count exceeding package max.
        """
        client = client_factory(business=authenticated_client.business)
        package = package_factory(business=authenticated_client.business, min_pax=50, max_pax=100)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'client': client.id,
            'package': package.id,
            'event_date': '2026-12-25',
            'pax_count': 150,
        }
        serializer = BookingCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'pax_count' in serializer.errors

    def test_pax_below_package_min(self, authenticated_client, client_factory, package_factory):
        """
        Should reject pax count below package min.
        """
        client = client_factory(business=authenticated_client.business)
        package = package_factory(business=authenticated_client.business, min_pax=50)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'client': client.id,
            'package': package.id,
            'event_date': '2026-12-25',
            'pax_count': 30,
        }
        serializer = BookingCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'pax_count' in serializer.errors

    def test_booking_without_package_allowed(self, authenticated_client, client_factory):
        """
        Should allow booking without package.
        """
        client = client_factory(business=authenticated_client.business)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'client': client.id,
            'event_date': '2026-12-25',
            'pax_count': 100,
            'total_amount': '5000.00',
        }
        serializer = BookingCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors


class TestBookingRescheduleRequestSerializer:
    """
    Tests for BookingRescheduleRequestSerializer.
    """

    def test_valid_reschedule_request(self):
        """
        Should validate correct reschedule data.
        """
        data = {
            'new_date': '2026-12-31',
            'new_time': '15:00:00',
            'reason': 'Client request',
        }
        serializer = BookingRescheduleRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_reschedule_without_time(self):
        """
        Should allow reschedule without new time.
        """
        data = {
            'new_date': '2026-12-31',
        }
        serializer = BookingRescheduleRequestSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_date_rejected(self):
        """
        Should reject invalid date format.
        """
        data = {
            'new_date': 'not-a-date',
        }
        serializer = BookingRescheduleRequestSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestBookingListSerializer:
    """
    Tests for BookingListSerializer.
    """

    def test_lightweight_serialization(self, booking_factory):
        """
        Should serialize only essential fields.
        """
        booking = booking_factory()

        serializer = BookingListSerializer(booking)
        data = serializer.data

        assert 'id' in data
        assert 'client_name' in data
        assert 'event_date' in data
        assert 'status' in data
        assert 'reschedules' not in data
