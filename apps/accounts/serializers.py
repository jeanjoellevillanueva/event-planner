"""
Serializers for accounts app.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import BusinessMembership
from apps.accounts.models import Invitation
from apps.common.timezone import TIMEZONE_CHOICES
from apps.common.timezone import is_valid_timezone

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'phone', 'timezone']

    def validate_timezone(self, value):
        """
        Validate timezone is a valid IANA timezone.
        """
        if not is_valid_timezone(value):
            raise serializers.ValidationError("Invalid timezone")
        return value

    def validate(self, attrs):
        """
        Validate passwords match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        """
        Create new user.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    """

    current_business_id = serializers.IntegerField(source='current_business.id', read_only=True)
    current_business_name = serializers.CharField(source='current_business.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'phone', 'timezone',
            'current_business_id', 'current_business_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']

    def validate_timezone(self, value):
        """
        Validate timezone is a valid IANA timezone.
        """
        if not is_valid_timezone(value):
            raise serializers.ValidationError("Invalid timezone")
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """

    class Meta:
        model = User
        fields = ['username', 'phone', 'timezone']

    def validate_timezone(self, value):
        """
        Validate timezone is a valid IANA timezone.
        """
        if not is_valid_timezone(value):
            raise serializers.ValidationError("Invalid timezone")
        return value


class BusinessMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for business membership.
    """

    business_id = serializers.IntegerField(source='business.id', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_type = serializers.CharField(source='business.business_type', read_only=True)

    class Meta:
        model = BusinessMembership
        fields = ['id', 'business_id', 'business_name', 'business_type', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class SwitchBusinessSerializer(serializers.Serializer):
    """
    Serializer for switching current business.
    """

    business_id = serializers.IntegerField()

    def validate_business_id(self, value):
        """
        Validate user has access to the business.
        """
        user = self.context['request'].user
        if not user.business_memberships.filter(business_id=value).exists():
            raise serializers.ValidationError("You do not have access to this business")
        return value


class InvitationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating invitations.
    """

    class Meta:
        model = Invitation
        fields = ['email', 'role']

    def validate_email(self, value):
        """
        Check if user already has membership in this business.
        """
        business = self.context['business']
        existing_user = User.objects.filter(email=value).first()

        if existing_user:
            if BusinessMembership.objects.filter(user=existing_user, business=business).exists():
                raise serializers.ValidationError("User is already a member of this business")

        pending_invitation = Invitation.objects.filter(
            email=value,
            business=business,
            status='pending'
        ).first()

        if pending_invitation and not pending_invitation.is_expired:
            raise serializers.ValidationError("A pending invitation already exists for this email")

        return value

    def create(self, validated_data):
        """
        Create invitation with business context.
        """
        validated_data['business'] = self.context['business']
        validated_data['invited_by'] = self.context['request'].user
        return super().create(validated_data)


class InvitationSerializer(serializers.ModelSerializer):
    """
    Serializer for invitation details.
    """

    business_name = serializers.CharField(source='business.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.username', read_only=True)

    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'role', 'token', 'status',
            'business_name', 'invited_by_name',
            'expires_at', 'accepted_at', 'created_at'
        ]
        read_only_fields = ['id', 'token', 'status', 'expires_at', 'accepted_at', 'created_at']


class InvitationAcceptSerializer(serializers.Serializer):
    """
    Serializer for accepting invitation (existing user).
    """

    pass


class InvitationRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering via invitation.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password_confirm', 'phone', 'timezone']

    def validate_timezone(self, value):
        """
        Validate timezone is a valid IANA timezone.
        """
        if not is_valid_timezone(value):
            raise serializers.ValidationError("Invalid timezone")
        return value

    def validate(self, attrs):
        """
        Validate passwords match.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        return attrs
