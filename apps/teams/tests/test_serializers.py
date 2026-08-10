"""
Tests for teams serializers.
"""

import pytest
from rest_framework.test import APIRequestFactory

from apps.accounts.models import BusinessMembership
from apps.teams.models import BookingAssignment
from apps.teams.models import TeamMember
from apps.teams.serializers import BookingAssignmentCreateSerializer
from apps.teams.serializers import BookingAssignmentSerializer
from apps.teams.serializers import TeamMemberCreateSerializer
from apps.teams.serializers import TeamMemberListSerializer
from apps.teams.serializers import TeamMemberSerializer


@pytest.mark.django_db
class TestTeamMemberSerializer:
    """
    Tests for TeamMemberSerializer.
    """

    def test_serialize_team_member(self, business_factory):
        """
        Should serialize team member with all fields.
        """
        business = business_factory()
        member = TeamMember.objects.create(
            business=business,
            name='John Coordinator',
            role='Coordinator',
            email='john@team.com',
            phone='1234567890'
        )

        serializer = TeamMemberSerializer(member)
        data = serializer.data

        assert data['name'] == 'John Coordinator'
        assert data['role'] == 'Coordinator'
        assert data['email'] == 'john@team.com'

    def test_serialize_team_member_with_user(self, business_factory, user_factory):
        """
        Should serialize team member linked to user.
        """
        business = business_factory()
        user = user_factory(email='linked@team.com')
        member = TeamMember.objects.create(
            business=business,
            user=user,
            name='Linked Member',
            role='Staff'
        )

        serializer = TeamMemberSerializer(member)
        data = serializer.data

        assert data['user_email'] == 'linked@team.com'


@pytest.mark.django_db
class TestTeamMemberCreateSerializer:
    """
    Tests for TeamMemberCreateSerializer.
    """

    def test_valid_team_member_creation(self, authenticated_client):
        """
        Should validate correct team member data.
        """
        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'name': 'New Member',
            'role': 'Photographer',
            'email': 'photo@team.com',
        }
        serializer = TeamMemberCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_link_to_business_member(self, authenticated_client, user_factory):
        """
        Should allow linking to existing business member.
        """
        member_user = user_factory(email='member@test.com')
        BusinessMembership.objects.create(
            user=member_user,
            business=authenticated_client.business,
            role='staff'
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'user': member_user.id,
            'name': 'Member User',
            'role': 'Coordinator',
        }
        serializer = TeamMemberCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_link_to_non_member_rejected(self, authenticated_client, user_factory):
        """
        Should reject linking to user not in business.
        """
        non_member = user_factory(email='nonmember@test.com')

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'user': non_member.id,
            'name': 'Non Member',
            'role': 'Coordinator',
        }
        serializer = TeamMemberCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'user' in serializer.errors


@pytest.mark.django_db
class TestBookingAssignmentSerializer:
    """
    Tests for BookingAssignmentSerializer.
    """

    def test_serialize_assignment(self, booking_factory, business_factory):
        """
        Should serialize assignment with related info.
        """
        business = business_factory()
        booking = booking_factory(business=business)
        member = TeamMember.objects.create(
            business=business,
            name='John',
            role='Coordinator'
        )
        assignment = BookingAssignment.objects.create(
            booking=booking,
            team_member=member,
            role='Lead Coordinator'
        )

        serializer = BookingAssignmentSerializer(assignment)
        data = serializer.data

        assert data['team_member_name'] == 'John'
        assert data['team_member_role'] == 'Coordinator'
        assert data['role'] == 'Lead Coordinator'


@pytest.mark.django_db
class TestBookingAssignmentCreateSerializer:
    """
    Tests for BookingAssignmentCreateSerializer.
    """

    def test_valid_assignment(self, authenticated_client):
        """
        Should validate correct assignment data.
        """
        member = TeamMember.objects.create(
            business=authenticated_client.business,
            name='John',
            role='Staff'
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'team_member': member.id,
            'role': 'Event Lead',
        }
        serializer = BookingAssignmentCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_member_from_other_business_rejected(self, authenticated_client, business_factory):
        """
        Should reject team member from different business.
        """
        other_business = business_factory(name='Other')
        other_member = TeamMember.objects.create(
            business=other_business,
            name='Other Member',
            role='Staff'
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'team_member': other_member.id,
        }
        serializer = BookingAssignmentCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'team_member' in serializer.errors


@pytest.mark.django_db
class TestTeamMemberListSerializer:
    """
    Tests for TeamMemberListSerializer.
    """

    def test_lightweight_serialization(self, business_factory):
        """
        Should serialize only essential fields.
        """
        business = business_factory()
        member = TeamMember.objects.create(
            business=business,
            name='John',
            role='Staff',
            email='john@test.com'
        )

        serializer = TeamMemberListSerializer(member)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'role' in data
        assert 'email' not in data
