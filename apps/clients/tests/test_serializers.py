"""
Tests for clients serializers.
"""

import pytest
from rest_framework.test import APIRequestFactory

from apps.clients.models import Client
from apps.clients.serializers import ClientCreateSerializer
from apps.clients.serializers import ClientListSerializer
from apps.clients.serializers import ClientSerializer


@pytest.mark.django_db
class TestClientSerializer:
    """
    Tests for ClientSerializer.
    """

    def test_serialize_client(self, client_factory):
        """
        Should serialize client with computed fields.
        """
        client = client_factory(
            name='Test Client',
            email='client@test.com',
            phone='1234567890'
        )

        serializer = ClientSerializer(client)
        data = serializer.data

        assert data['name'] == 'Test Client'
        assert data['email'] == 'client@test.com'
        assert 'booking_count' in data
        assert 'total_spent' in data

    def test_booking_count_computed(self, client_factory, booking_factory):
        """
        Should compute correct booking count.
        """
        client = client_factory()
        booking_factory(client=client, business=client.business)
        booking_factory(client=client, business=client.business)

        serializer = ClientSerializer(client)
        assert serializer.data['booking_count'] == 2


@pytest.mark.django_db
class TestClientCreateSerializer:
    """
    Tests for ClientCreateSerializer.
    """

    def test_valid_client_creation(self, authenticated_client):
        """
        Should validate correct client data.
        """
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'New Client',
            'email': 'new@client.com',
            'phone': '9876543210',
        }
        serializer = ClientCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_duplicate_email_rejected(self, authenticated_client, client_factory):
        """
        Should reject duplicate email within same business.
        """
        existing = client_factory(
            business=authenticated_client.business,
            email='existing@client.com'
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'New Client',
            'email': 'existing@client.com',
        }
        serializer = ClientCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_same_email_different_business_allowed(self, authenticated_client, business_factory, client_factory):
        """
        Should allow same email in different businesses.
        """
        other_business = business_factory(name='Other Business')
        client_factory(business=other_business, email='shared@client.com')

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'New Client',
            'email': 'shared@client.com',
        }
        serializer = ClientCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()


@pytest.mark.django_db
class TestClientListSerializer:
    """
    Tests for ClientListSerializer.
    """

    def test_lightweight_serialization(self, client_factory):
        """
        Should serialize only essential fields.
        """
        client = client_factory()

        serializer = ClientListSerializer(client)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'email' in data
        assert 'booking_count' not in data
        assert 'total_spent' not in data
