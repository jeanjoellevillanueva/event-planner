"""
Tests for accounts serializers.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.accounts.models import BusinessMembership
from apps.accounts.models import Invitation
from apps.accounts.serializers import BusinessMembershipSerializer
from apps.accounts.serializers import InvitationCreateSerializer
from apps.accounts.serializers import SwitchBusinessSerializer
from apps.accounts.serializers import UserRegistrationSerializer
from apps.accounts.serializers import UserSerializer
from apps.accounts.serializers import UserUpdateSerializer

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """
    Tests for UserRegistrationSerializer.
    """

    def test_valid_registration(self):
        """
        Should validate correct registration data.
        """
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'timezone': 'Asia/Manila',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_password_mismatch(self):
        """
        Should reject mismatched passwords.
        """
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass!',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors

    def test_invalid_timezone(self):
        """
        Should reject invalid timezone.
        """
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'timezone': 'Invalid/Timezone',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'timezone' in serializer.errors

    def test_weak_password(self):
        """
        Should reject weak passwords.
        """
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': '123',
            'password_confirm': '123',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_create_user(self):
        """
        Should create user with hashed password.
        """
        data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'timezone': 'UTC',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()

        assert user.email == 'test@example.com'
        assert user.check_password('SecurePass123!')
        assert user.timezone == 'UTC'


@pytest.mark.django_db
class TestUserSerializer:
    """
    Tests for UserSerializer.
    """

    def test_serialize_user(self, user_factory, business_factory):
        """
        Should serialize user with business info.
        """
        user = user_factory(timezone='Asia/Manila')
        business = business_factory()
        user.current_business = business
        user.save()

        serializer = UserSerializer(user)
        data = serializer.data

        assert data['email'] == user.email
        assert data['timezone'] == 'Asia/Manila'
        assert data['current_business_id'] == business.id
        assert data['current_business_name'] == business.name

    def test_read_only_fields(self, user_factory):
        """
        Should not allow updating read-only fields.
        """
        user = user_factory()
        serializer = UserSerializer(user, data={'email': 'new@example.com'}, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.email != 'new@example.com'


@pytest.mark.django_db
class TestUserUpdateSerializer:
    """
    Tests for UserUpdateSerializer.
    """

    def test_update_timezone(self, user_factory):
        """
        Should update user timezone.
        """
        user = user_factory()
        serializer = UserUpdateSerializer(user, data={'timezone': 'America/New_York'}, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.timezone == 'America/New_York'

    def test_invalid_timezone_rejected(self, user_factory):
        """
        Should reject invalid timezone on update.
        """
        user = user_factory()
        serializer = UserUpdateSerializer(user, data={'timezone': 'Bad/Zone'}, partial=True)
        assert not serializer.is_valid()
        assert 'timezone' in serializer.errors


@pytest.mark.django_db
class TestSwitchBusinessSerializer:
    """
    Tests for SwitchBusinessSerializer.
    """

    def test_valid_business_switch(self, user_factory, business_factory):
        """
        Should allow switching to accessible business.
        """
        user = user_factory()
        business = business_factory()
        BusinessMembership.objects.create(user=user, business=business, role='admin')

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user

        serializer = SwitchBusinessSerializer(
            data={'business_id': business.id},
            context={'request': request}
        )
        assert serializer.is_valid()

    def test_inaccessible_business_rejected(self, user_factory, business_factory):
        """
        Should reject switching to inaccessible business.
        """
        user = user_factory()
        business = business_factory()

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user

        serializer = SwitchBusinessSerializer(
            data={'business_id': business.id},
            context={'request': request}
        )
        assert not serializer.is_valid()
        assert 'business_id' in serializer.errors


@pytest.mark.django_db
class TestInvitationCreateSerializer:
    """
    Tests for InvitationCreateSerializer.
    """

    def test_valid_invitation(self, user_factory, business_factory):
        """
        Should create valid invitation.
        """
        user = user_factory()
        business = business_factory()

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user

        serializer = InvitationCreateSerializer(
            data={'email': 'invite@example.com', 'role': 'admin'},
            context={'request': request, 'business': business}
        )
        assert serializer.is_valid(), serializer.errors

    def test_existing_member_rejected(self, user_factory, business_factory):
        """
        Should reject invitation if user is already a member.
        """
        existing_user = user_factory(email='existing@example.com')
        business = business_factory()
        BusinessMembership.objects.create(user=existing_user, business=business, role='staff')

        inviter = user_factory(email='inviter@example.com')
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = inviter

        serializer = InvitationCreateSerializer(
            data={'email': 'existing@example.com', 'role': 'admin'},
            context={'request': request, 'business': business}
        )
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_pending_invitation_rejected(self, user_factory, business_factory):
        """
        Should reject if pending invitation exists.
        """
        user = user_factory()
        business = business_factory()

        Invitation.objects.create(
            business=business,
            email='pending@example.com',
            role='admin',
            invited_by=user,
            status='pending'
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user

        serializer = InvitationCreateSerializer(
            data={'email': 'pending@example.com', 'role': 'admin'},
            context={'request': request, 'business': business}
        )
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
