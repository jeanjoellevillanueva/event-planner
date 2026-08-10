"""
Tests for store/business switching.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import BusinessMembership


@pytest.mark.django_db
class TestStoreSwitching:
    """
    Tests for business switching functionality.
    """

    def test_list_user_businesses(self, authenticated_client, business_factory):
        """
        Should list all businesses user belongs to.
        """
        second_business = business_factory(name='Second Business')
        BusinessMembership.objects.create(
            user=authenticated_client.user,
            business=second_business,
            role='admin'
        )

        url = reverse('user_businesses')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_switch_business_success(self, authenticated_client, business_factory):
        """
        Should switch to another business user belongs to.
        """
        second_business = business_factory(name='Second Business')
        BusinessMembership.objects.create(
            user=authenticated_client.user,
            business=second_business,
            role='admin'
        )

        url = reverse('switch_business')
        data = {'business_id': second_business.id}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['current_business']['id'] == second_business.id

        authenticated_client.user.refresh_from_db()
        assert authenticated_client.user.current_business == second_business

    def test_switch_business_unauthorized(self, authenticated_client, business_factory):
        """
        Should reject switching to business user doesn't belong to.
        """
        other_business = business_factory(name='Other Business')

        url = reverse('switch_business')
        data = {'business_id': other_business.id}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
