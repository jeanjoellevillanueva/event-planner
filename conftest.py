"""
Pytest configuration and fixtures.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user_factory(db):
    """
    Factory for creating test users.
    """
    def create_user(email='test@example.com', password='testpass123', **kwargs):
        defaults = {
            'username': email.split('@')[0],
            'timezone': 'UTC',
        }
        defaults.update(kwargs)
        user = User.objects.create_user(email=email, password=password, **defaults)
        return user
    return create_user


@pytest.fixture
def business_factory(db):
    """
    Factory for creating test businesses.
    """
    def create_business(name='Test Business', **kwargs):
        from apps.businesses.models import Business
        defaults = {
            'business_type': 'event',
            'email': 'business@example.com',
        }
        defaults.update(kwargs)
        return Business.objects.create(name=name, **defaults)
    return create_business


@pytest.fixture
def client_factory(db, business_factory):
    """
    Factory for creating test clients.
    """
    def create_client(business=None, name='Test Client', **kwargs):
        from apps.clients.models import Client
        if business is None:
            business = business_factory()
        defaults = {
            'email': 'client@example.com',
            'phone': '1234567890',
        }
        defaults.update(kwargs)
        return Client.objects.create(business=business, name=name, **defaults)
    return create_client


@pytest.fixture
def package_factory(db, business_factory):
    """
    Factory for creating test packages.
    """
    def create_package(business=None, name='Test Package', **kwargs):
        from apps.products.models import Package
        if business is None:
            business = business_factory()
        defaults = {
            'base_price': 10000,
            'min_pax': 50,
            'max_pax': 200,
        }
        defaults.update(kwargs)
        return Package.objects.create(business=business, name=name, **defaults)
    return create_package


@pytest.fixture
def booking_factory(db, business_factory, client_factory, package_factory):
    """
    Factory for creating test bookings.
    """
    def create_booking(business=None, client=None, package=None, **kwargs):
        from datetime import date
        from apps.bookings.models import Booking

        if business is None:
            business = business_factory()
        if client is None:
            client = client_factory(business=business)
        if package is None:
            package = package_factory(business=business)

        defaults = {
            'event_date': date(2026, 12, 25),
            'venue': 'Test Venue',
            'pax_count': 100,
            'total_amount': 15000,
        }
        defaults.update(kwargs)
        return Booking.objects.create(
            business=business,
            client=client,
            package=package,
            **defaults
        )
    return create_booking


@pytest.fixture
def api_client():
    """
    DRF API client.
    """
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user_factory, business_factory):
    """
    Authenticated API client with user and business.
    """
    from apps.accounts.models import BusinessMembership

    user = user_factory()
    business = business_factory()

    BusinessMembership.objects.create(
        user=user,
        business=business,
        role='owner'
    )

    user.current_business = business
    user.save()

    api_client.force_authenticate(user=user)
    api_client.user = user
    api_client.business = business

    return api_client
