"""
Tests for authentication endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUserRegistration:
    """
    Tests for user registration.
    """

    def test_register_user_success(self, api_client):
        """
        Should register user with valid data.
        """
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'timezone': 'Asia/Manila',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user']['email'] == 'newuser@example.com'
        assert response.data['user']['timezone'] == 'Asia/Manila'

    def test_register_user_password_mismatch(self, api_client):
        """
        Should reject registration with mismatched passwords.
        """
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_register_user_invalid_timezone(self, api_client):
        """
        Should reject registration with invalid timezone.
        """
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'timezone': 'Invalid/Timezone',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'timezone' in response.data

    def test_register_user_duplicate_email(self, api_client, user_factory):
        """
        Should reject registration with existing email.
        """
        user_factory(email='existing@example.com')

        url = reverse('register')
        data = {
            'email': 'existing@example.com',
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """
    Tests for user login.
    """

    def test_login_success(self, api_client, user_factory):
        """
        Should return tokens for valid credentials.
        """
        user_factory(email='test@example.com', password='testpass123')

        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_credentials(self, api_client, user_factory):
        """
        Should reject invalid credentials.
        """
        user_factory(email='test@example.com', password='testpass123')

        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword',
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfile:
    """
    Tests for user profile endpoints.
    """

    def test_get_profile(self, authenticated_client):
        """
        Should return current user profile.
        """
        url = reverse('user_profile')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == authenticated_client.user.email

    def test_update_timezone(self, authenticated_client):
        """
        Should update user timezone.
        """
        url = reverse('user_profile')
        data = {'timezone': 'America/New_York'}

        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK

        authenticated_client.user.refresh_from_db()
        assert authenticated_client.user.timezone == 'America/New_York'
