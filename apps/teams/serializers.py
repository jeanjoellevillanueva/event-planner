"""
Serializers for teams app.
"""

from rest_framework import serializers

from apps.common.mixins import TimezoneAwareMixin
from apps.teams.models import BookingAssignment
from apps.teams.models import TeamMember


class TeamMemberSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for TeamMember model.
    """

    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            'id', 'user', 'user_email', 'name', 'email', 'phone',
            'role', 'availability', 'hourly_rate', 'notes', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeamMemberCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating team members.
    """

    class Meta:
        model = TeamMember
        fields = [
            'user', 'name', 'email', 'phone',
            'role', 'availability', 'hourly_rate', 'notes'
        ]

    def validate_user(self, value):
        """
        Ensure user belongs to the business.
        """
        if value is None:
            return value

        business = self.context['request'].user.current_business
        if not value.business_memberships.filter(business=business).exists():
            raise serializers.ValidationError("User is not a member of this business")
        return value


class TeamMemberListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for team member lists.
    """

    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'role', 'is_active']


class BookingAssignmentSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for BookingAssignment model.
    """

    team_member_name = serializers.CharField(source='team_member.name', read_only=True)
    team_member_role = serializers.CharField(source='team_member.role', read_only=True)
    booking_event_date = serializers.DateField(source='booking.event_date', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.username', read_only=True)

    class Meta:
        model = BookingAssignment
        fields = [
            'id', 'booking', 'team_member', 'team_member_name', 'team_member_role',
            'booking_event_date', 'role', 'notes',
            'assigned_by', 'assigned_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'assigned_by', 'created_at']


class BookingAssignmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating booking assignments.
    """

    class Meta:
        model = BookingAssignment
        fields = ['team_member', 'role', 'notes']

    def validate_team_member(self, value):
        """
        Ensure team member belongs to the business.
        """
        business = self.context['request'].user.current_business
        if value.business != business:
            raise serializers.ValidationError("Team member does not belong to your business")
        return value
