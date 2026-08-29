"""
Tests for the Tailwind web UI.
"""

from datetime import date
from datetime import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

import pytest
from django.test import Client as DjangoClient
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import BusinessMembership
from apps.accounts.models import Invitation
from apps.bookings.models import Booking
from apps.clients.models import Client
from apps.reminders.models import Reminder


@pytest.mark.django_db
class TestWebAuthViews:
    """
    Tests for register, login, and business onboarding.
    """

    def test_home_redirects_anonymous_users_to_login(self):
        """
        The root URL should send guests to login.
        """
        response = DjangoClient().get('/')
        assert response.status_code == 302
        assert response.url == reverse('web_login')

    def test_register_creates_user_and_requires_business(self):
        """
        Registration should log the user in and send them to create a store.
        """
        client = DjangoClient()
        response = client.post(reverse('web_register'), {
            'email': 'owner@example.com',
            'username': 'owner',
            'timezone': 'Asia/Manila',
            'password': 'StrongPass123',
            'password_confirm': 'StrongPass123',
        })
        assert response.status_code == 302
        assert response.url == reverse('web_business_create')

        follow = client.get(reverse('web_dashboard'))
        assert follow.status_code == 302
        assert follow.url == reverse('web_business_create')

    def test_login_rejects_bad_password(self, user_factory):
        """
        Bad credentials should stay on the login page.
        """
        user_factory(email='owner@example.com', password='right-password')
        response = DjangoClient().post(reverse('web_login'), {
            'email': 'owner@example.com',
            'password': 'wrong-password',
        })
        assert response.status_code == 200
        assert b'Invalid email or password' in response.content


@pytest.mark.django_db
class TestWebStoreViews:
    """
    Tests for dashboard, clients, calendar, and invites.
    """

    def logged_in_owner(self, user_factory, business_factory):
        """
        Build an owner session for the current business.
        """
        user = user_factory(email='owner@example.com', timezone='Asia/Manila')
        business = business_factory(name='Manila Events')
        BusinessMembership.objects.create(user=user, business=business, role='owner')
        user.current_business = business
        user.save(update_fields=['current_business'])
        client = DjangoClient()
        client.force_login(user)
        return client, user, business

    def test_dashboard_shows_business_stats(self, user_factory, business_factory, client_factory):
        """
        Dashboard should render store stats for the current business.
        """
        client, user, business = self.logged_in_owner(user_factory, business_factory)
        client_factory(business=business, name='Ada Lovelace')
        response = client.get(reverse('web_dashboard'))
        assert response.status_code == 200
        assert b'Manila Events' in response.content
        assert response.context['stats']['total_clients'] == 1

    def test_create_client_from_web_form(self, user_factory, business_factory):
        """
        Owners should be able to add a client from the web UI.
        """
        client, user, business = self.logged_in_owner(user_factory, business_factory)
        response = client.post(reverse('web_client_create'), {
            'name': 'Ada Lovelace',
            'email': 'ada@example.com',
            'phone': '555-0100',
            'is_active': 'on',
        })
        assert response.status_code == 302
        assert Client.objects.filter(business=business, name='Ada Lovelace').exists()

    def test_calendar_lists_booking_on_event_date(
        self,
        user_factory,
        business_factory,
        booking_factory,
    ):
        """
        Calendar should include a booking on its event date.
        """
        client, user, business = self.logged_in_owner(user_factory, business_factory)
        booking = booking_factory(
            business=business,
            event_date=date(2026, 12, 25),
        )
        response = client.get(reverse('web_calendar'), {'year': 2026, 'month': 12})
        assert response.status_code == 200
        found = False
        for week in response.context['calendar_weeks']:
            for day in week:
                if day['date'] == date(2026, 12, 25):
                    found = booking in day['bookings']
        assert found

    def test_reschedule_updates_booking_date(
        self,
        user_factory,
        business_factory,
        booking_factory,
    ):
        """
        Reschedule form should move a pending booking.
        """
        client, user, business = self.logged_in_owner(user_factory, business_factory)
        booking = booking_factory(business=business, event_date=date(2026, 12, 25))
        response = client.post(reverse('web_booking_reschedule', args=[booking.pk]), {
            'new_date': '2026-12-31',
            'reason': 'Venue change',
        })
        assert response.status_code == 302
        booking.refresh_from_db()
        assert booking.event_date == date(2026, 12, 31)

    def test_staff_cannot_open_invite_page(self, user_factory, business_factory):
        """
        Staff should be blocked from the invite page.
        """
        user = user_factory(email='staff@example.com')
        business = business_factory()
        BusinessMembership.objects.create(user=user, business=business, role='staff')
        user.current_business = business
        user.save(update_fields=['current_business'])
        client = DjangoClient()
        client.force_login(user)
        response = client.get(reverse('web_invite_create'))
        assert response.status_code == 302
        assert response.url == reverse('web_dashboard')

    def test_switch_business_changes_current_store(self, user_factory, business_factory):
        """
        Store switch should update current_business.
        """
        user = user_factory()
        first = business_factory(name='First Store')
        second = business_factory(name='Second Store')
        BusinessMembership.objects.create(user=user, business=first, role='owner')
        BusinessMembership.objects.create(user=user, business=second, role='admin')
        user.current_business = first
        user.save(update_fields=['current_business'])
        client = DjangoClient()
        client.force_login(user)
        response = client.post(reverse('web_switch_business'), {'business': second.pk})
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.current_business_id == second.pk

    def test_invitation_register_joins_business(self, user_factory, business_factory):
        """
        A new user should join the invited business from the accept page.
        """
        owner = user_factory(email='boss@example.com')
        business = business_factory(name='Invited Store')
        invitation = Invitation.objects.create(
            business=business,
            email='newhire@example.com',
            role='staff',
            invited_by=owner,
            expires_at=timezone.now() + timedelta(days=3),
        )
        client = DjangoClient()
        response = client.post(reverse('web_invitation_accept', args=[invitation.token]), {
            'username': 'newhire',
            'timezone': 'UTC',
            'password': 'StrongPass123',
            'password_confirm': 'StrongPass123',
        })
        assert response.status_code == 302
        invitation.refresh_from_db()
        assert invitation.status == 'accepted'
        assert BusinessMembership.objects.filter(
            business=business,
            user__email='newhire@example.com',
            role='staff',
        ).exists()

    def test_reminder_form_stores_scheduled_time_in_utc(
        self,
        user_factory,
        business_factory,
        booking_factory,
    ):
        """
        Naive reminder times should be saved as UTC from the user timezone.
        """
        client, user, business = self.logged_in_owner(user_factory, business_factory)
        booking = booking_factory(business=business)
        response = client.post(reverse('web_reminder_create'), {
            'booking': booking.pk,
            'reminder_type': 'email',
            'scheduled_at': '2026-08-10T14:00',
            'subject': 'Event soon',
            'message': 'See you tomorrow',
            'recipient_email': 'client@example.com',
        })
        assert response.status_code == 302
        reminder = Reminder.objects.get(booking=booking)
        assert reminder.scheduled_at == datetime(2026, 8, 10, 6, 0, tzinfo=ZoneInfo('UTC'))

    def test_login_rejects_external_next_url(self, user_factory):
        """
        Login should ignore open-redirect next URLs.
        """
        user_factory(email='owner@example.com', password='StrongPass123')
        response = DjangoClient().post(
            reverse('web_login') + '?next=https://evil.example/phish',
            {'email': 'owner@example.com', 'password': 'StrongPass123'},
        )
        assert response.status_code == 302
        assert response.url == reverse('web_dashboard')

    def test_stale_current_business_is_rejected(self, user_factory, business_factory):
        """
        Users should not keep access after membership is removed.
        """
        user = user_factory()
        business = business_factory()
        user.current_business = business
        user.save(update_fields=['current_business'])
        client = DjangoClient()
        client.force_login(user)
        response = client.get(reverse('web_dashboard'))
        assert response.status_code == 302
        assert response.url == reverse('web_business_create')

    def test_staff_cannot_create_products(self, user_factory, business_factory):
        """
        Staff should be blocked from product create, matching the API.
        """
        user = user_factory(email='staff@example.com')
        business = business_factory()
        BusinessMembership.objects.create(user=user, business=business, role='staff')
        user.current_business = business
        user.save(update_fields=['current_business'])
        client = DjangoClient()
        client.force_login(user)
        response = client.get(reverse('web_product_create'))
        assert response.status_code == 302
        assert response.url == reverse('web_dashboard')

    def test_invite_accept_does_not_change_existing_membership(
        self,
        user_factory,
        business_factory,
    ):
        """
        Existing members should not be demoted by a later invite.
        """
        user = user_factory(email='owner@example.com')
        inviter = user_factory(email='boss@example.com', username='boss')
        business = business_factory()
        BusinessMembership.objects.create(user=user, business=business, role='owner')
        user.current_business = business
        user.save(update_fields=['current_business'])
        invitation = Invitation.objects.create(
            business=business,
            email=user.email,
            role='staff',
            invited_by=inviter,
            expires_at=timezone.now() + timedelta(days=3),
        )
        client = DjangoClient()
        client.force_login(user)
        response = client.post(reverse('web_invitation_accept', args=[invitation.token]))
        assert response.status_code == 302
        membership = BusinessMembership.objects.get(user=user, business=business)
        assert membership.role == 'owner'
        invitation.refresh_from_db()
        assert invitation.status == 'pending'

    def test_calendar_today_uses_user_timezone(self, user_factory, business_factory):
        """
        Calendar today should follow the user's timezone, not UTC.
        """
        user = user_factory(email='owner@example.com', timezone='Pacific/Auckland')
        business = business_factory()
        BusinessMembership.objects.create(user=user, business=business, role='owner')
        user.current_business = business
        user.save(update_fields=['current_business'])
        client = DjangoClient()
        client.force_login(user)
        response = client.get(reverse('web_calendar'))
        assert response.status_code == 200
        assert response.context['today'] == timezone.now().astimezone(
            ZoneInfo('Pacific/Auckland')
        ).date()

    def test_web_pages_do_not_return_json_without_business(self, user_factory):
        """
        Users without a store should get the create-business page, not API JSON.
        """
        user = user_factory()
        client = DjangoClient()
        client.force_login(user)
        response = client.get(reverse('web_business_create'))
        assert response.status_code == 200
        assert b'Create business' in response.content
