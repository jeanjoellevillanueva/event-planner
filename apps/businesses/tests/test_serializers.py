"""
Tests for businesses serializers.
"""

import pytest

from apps.businesses.models import Business
from apps.businesses.serializers import BusinessCreateSerializer
from apps.businesses.serializers import BusinessDashboardSerializer
from apps.businesses.serializers import BusinessSerializer


@pytest.mark.django_db
class TestBusinessSerializer:
    """
    Tests for BusinessSerializer.
    """

    def test_serialize_business(self, business_factory):
        """
        Should serialize business with all fields.
        """
        business = business_factory(
            name='Test Business',
            business_type='event',
            email='test@business.com'
        )

        serializer = BusinessSerializer(business)
        data = serializer.data

        assert data['name'] == 'Test Business'
        assert data['business_type'] == 'event'
        assert data['email'] == 'test@business.com'
        assert 'slug' in data
        assert 'created_at' in data

    def test_slug_is_readonly(self, business_factory):
        """
        Should not allow updating slug.
        """
        business = business_factory()
        original_slug = business.slug

        serializer = BusinessSerializer(
            business,
            data={'slug': 'new-slug'},
            partial=True
        )
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.slug == original_slug


@pytest.mark.django_db
class TestBusinessCreateSerializer:
    """
    Tests for BusinessCreateSerializer.
    """

    def test_valid_business_creation(self):
        """
        Should validate correct business data.
        """
        data = {
            'name': 'New Business',
            'business_type': 'catering',
            'email': 'contact@newbusiness.com',
        }
        serializer = BusinessCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_business_type(self):
        """
        Should reject invalid business type.
        """
        data = {
            'name': 'New Business',
            'business_type': 'invalid_type',
        }
        serializer = BusinessCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'business_type' in serializer.errors

    def test_create_generates_slug(self):
        """
        Should auto-generate slug on create.
        """
        data = {
            'name': 'My Amazing Business',
            'business_type': 'event',
        }
        serializer = BusinessCreateSerializer(data=data)
        assert serializer.is_valid()
        business = serializer.save()

        assert business.slug == 'my-amazing-business'


class TestBusinessDashboardSerializer:
    """
    Tests for BusinessDashboardSerializer.
    """

    def test_serialize_dashboard_stats(self):
        """
        Should serialize dashboard statistics.
        """
        stats = {
            'total_clients': 50,
            'total_bookings': 100,
            'pending_bookings': 10,
            'confirmed_bookings': 80,
            'upcoming_events': 5,
            'monthly_bookings': 20,
            'total_products': 30,
            'total_packages': 10,
            'team_members': 8,
            'monthly_revenue': 150000.00,
        }

        serializer = BusinessDashboardSerializer(stats)
        data = serializer.data

        assert data['total_clients'] == 50
        assert data['monthly_revenue'] == '150000.00'
