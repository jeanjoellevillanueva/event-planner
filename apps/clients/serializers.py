"""
Serializers for clients app.
"""

from rest_framework import serializers

from apps.clients.models import Client
from apps.common.mixins import TimezoneAwareMixin


class ClientSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for Client model.
    """

    booking_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'phone', 'secondary_phone',
            'address', 'city', 'notes', 'is_active',
            'booking_count', 'total_spent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_booking_count(self, obj):
        """
        Get total booking count for client.
        """
        return obj.get_booking_count()

    def get_total_spent(self, obj):
        """
        Get total spent by client.
        """
        return obj.get_total_spent()


class ClientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating clients.
    """

    class Meta:
        model = Client
        fields = [
            'name', 'email', 'phone', 'secondary_phone',
            'address', 'city', 'notes'
        ]

    def validate_email(self, value):
        """
        Check for duplicate email within business.
        """
        if not value:
            return value

        business = self.context['request'].user.current_business
        existing = Client.objects.filter(
            business=business,
            email=value
        )

        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise serializers.ValidationError(
                "A client with this email already exists in this business"
            )
        return value


class ClientListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for client lists.
    """

    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'city', 'is_active']
