"""
Tests for accounts models.
"""

import pytest
from datetime import timedelta
from django.utils import timezone

from apps.accounts.models import BusinessMembership
from apps.accounts.models import Invitation


@pytest.mark.django_db
class TestUserModel:
    """
    Tests for User model.
    """

    def test_create_user(self, user_factory):
        """
        Should create user with correct fields.
        """
        user = user_factory(email='test@example.com', timezone='Asia/Manila')

        assert user.email == 'test@example.com'
        assert user.timezone == 'Asia/Manila'
        assert str(user) == 'test@example.com'

    def test_get_businesses(self, user_factory, business_factory):
        """
        Should return all user's businesses.
        """
        user = user_factory()
        business1 = business_factory(name='Business 1')
        business2 = business_factory(name='Business 2')

        BusinessMembership.objects.create(user=user, business=business1, role='owner')
        BusinessMembership.objects.create(user=user, business=business2, role='admin')

        businesses = user.get_businesses()
        assert len(businesses) == 2

    def test_get_role_for_business(self, user_factory, business_factory):
        """
        Should return correct role for business.
        """
        user = user_factory()
        business = business_factory()
        BusinessMembership.objects.create(user=user, business=business, role='admin')

        assert user.get_role_for_business(business) == 'admin'

    def test_get_role_for_unjoined_business(self, user_factory, business_factory):
        """
        Should return None for business user doesn't belong to.
        """
        user = user_factory()
        business = business_factory()

        assert user.get_role_for_business(business) is None


@pytest.mark.django_db
class TestBusinessMembershipModel:
    """
    Tests for BusinessMembership model.
    """

    def test_create_membership(self, user_factory, business_factory):
        """
        Should create membership with correct fields.
        """
        user = user_factory()
        business = business_factory()

        membership = BusinessMembership.objects.create(
            user=user,
            business=business,
            role='owner'
        )

        assert membership.role == 'owner'
        assert str(membership) == f'{user.email} - {business.name} (owner)'

    def test_unique_user_business(self, user_factory, business_factory):
        """
        Should enforce unique user-business combination.
        """
        user = user_factory()
        business = business_factory()

        BusinessMembership.objects.create(user=user, business=business, role='owner')

        with pytest.raises(Exception):
            BusinessMembership.objects.create(user=user, business=business, role='admin')


@pytest.mark.django_db
class TestInvitationModel:
    """
    Tests for Invitation model.
    """

    def test_create_invitation(self, user_factory, business_factory):
        """
        Should create invitation with expiry.
        """
        user = user_factory()
        business = business_factory()

        invitation = Invitation.objects.create(
            business=business,
            email='invite@example.com',
            role='admin',
            invited_by=user
        )

        assert invitation.status == 'pending'
        assert invitation.expires_at is not None
        assert invitation.token is not None

    def test_is_expired(self, user_factory, business_factory):
        """
        Should detect expired invitation.
        """
        user = user_factory()
        business = business_factory()

        invitation = Invitation.objects.create(
            business=business,
            email='invite@example.com',
            role='admin',
            invited_by=user,
            expires_at=timezone.now() - timedelta(days=1)
        )

        assert invitation.is_expired is True

    def test_is_valid(self, user_factory, business_factory):
        """
        Should detect valid invitation.
        """
        user = user_factory()
        business = business_factory()

        invitation = Invitation.objects.create(
            business=business,
            email='invite@example.com',
            role='admin',
            invited_by=user
        )

        assert invitation.is_valid is True

    def test_accepted_invitation_not_valid(self, user_factory, business_factory):
        """
        Should not be valid after acceptance.
        """
        user = user_factory()
        business = business_factory()

        invitation = Invitation.objects.create(
            business=business,
            email='invite@example.com',
            role='admin',
            invited_by=user,
            status='accepted'
        )

        assert invitation.is_valid is False
