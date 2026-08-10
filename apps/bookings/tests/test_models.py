"""
Tests for bookings models.
"""

import pytest
from datetime import date

from apps.bookings.models import Booking
from apps.bookings.models import BookingReschedule


@pytest.mark.django_db
class TestBookingModel:
    """
    Tests for Booking model.
    """

    def test_balance_amount_calculated(self, booking_factory):
        """
        Should auto-calculate balance amount.
        """
        booking = booking_factory(total_amount=10000, deposit_amount=3000)

        assert booking.balance_amount == 7000

    def test_can_reschedule_pending(self, booking_factory):
        """
        Should allow reschedule of pending booking.
        """
        booking = booking_factory(status='pending')
        assert booking.can_reschedule() is True

    def test_can_reschedule_confirmed(self, booking_factory):
        """
        Should allow reschedule of confirmed booking.
        """
        booking = booking_factory(status='confirmed')
        assert booking.can_reschedule() is True

    def test_cannot_reschedule_completed(self, booking_factory):
        """
        Should not allow reschedule of completed booking.
        """
        booking = booking_factory(status='completed')
        assert booking.can_reschedule() is False

    def test_cannot_reschedule_cancelled(self, booking_factory):
        """
        Should not allow reschedule of cancelled booking.
        """
        booking = booking_factory(status='cancelled')
        assert booking.can_reschedule() is False

    def test_reschedule_creates_audit(self, booking_factory, user_factory):
        """
        Should create reschedule audit record.
        """
        user = user_factory()
        booking = booking_factory(event_date=date(2026, 12, 25), status='confirmed')

        booking.reschedule(
            new_date=date(2026, 12, 31),
            reason='Client request',
            approved_by=user
        )

        assert booking.event_date == date(2026, 12, 31)
        assert booking.reschedules.count() == 1

        reschedule = booking.reschedules.first()
        assert reschedule.old_date == date(2026, 12, 25)
        assert reschedule.new_date == date(2026, 12, 31)
        assert reschedule.reason == 'Client request'

    def test_reschedule_completed_raises(self, booking_factory):
        """
        Should raise error when rescheduling completed booking.
        """
        booking = booking_factory(status='completed')

        with pytest.raises(ValueError):
            booking.reschedule(new_date=date(2026, 12, 31))


@pytest.mark.django_db
class TestBookingRescheduleModel:
    """
    Tests for BookingReschedule model.
    """

    def test_str_representation(self, booking_factory):
        """
        Should have readable string representation.
        """
        booking = booking_factory()
        reschedule = BookingReschedule.objects.create(
            booking=booking,
            old_date=date(2026, 12, 25),
            new_date=date(2026, 12, 31)
        )

        assert '2026-12-25' in str(reschedule)
        assert '2026-12-31' in str(reschedule)
