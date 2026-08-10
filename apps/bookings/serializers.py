"""
Serializers for bookings app.
"""

from rest_framework import serializers

from apps.bookings.models import Booking
from apps.bookings.models import BookingReschedule
from apps.common.mixins import TimezoneAwareMixin
from apps.common.timezone import is_valid_timezone


class BookingRescheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for BookingReschedule model.
    """

    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)

    class Meta:
        model = BookingReschedule
        fields = [
            'id', 'old_date', 'old_time', 'new_date', 'new_time',
            'reason', 'approved_by', 'approved_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'old_date', 'old_time', 'approved_by', 'created_at']


class BookingSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for Booking model.
    """

    client_name = serializers.CharField(source='client.name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    reschedules = BookingRescheduleSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'client', 'client_name', 'package', 'package_name',
            'event_date', 'event_time', 'event_end_time',
            'venue', 'venue_address', 'pax_count', 'status',
            'total_amount', 'deposit_amount', 'balance_amount',
            'notes', 'special_requests', 'reschedules',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'balance_amount', 'created_by', 'created_at', 'updated_at']


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating bookings.
    """

    class Meta:
        model = Booking
        fields = [
            'client', 'package', 'event_date', 'event_time', 'event_end_time',
            'venue', 'venue_address', 'pax_count', 'status',
            'total_amount', 'deposit_amount', 'notes', 'special_requests'
        ]

    def validate_client(self, value):
        """
        Ensure client belongs to user's business.
        """
        business = self.context['request'].user.current_business
        if value.business != business:
            raise serializers.ValidationError("Client does not belong to your business")
        return value

    def validate_package(self, value):
        """
        Ensure package belongs to user's business.
        """
        if value is None:
            return value

        business = self.context['request'].user.current_business
        if value.business != business:
            raise serializers.ValidationError("Package does not belong to your business")
        return value

    def validate(self, attrs):
        """
        Validate pax count against package limits.
        """
        package = attrs.get('package')
        pax_count = attrs.get('pax_count', 1)

        if package:
            if package.max_pax and pax_count > package.max_pax:
                raise serializers.ValidationError({
                    'pax_count': f'Maximum pax for this package is {package.max_pax}'
                })
            if pax_count < package.min_pax:
                raise serializers.ValidationError({
                    'pax_count': f'Minimum pax for this package is {package.min_pax}'
                })

        return attrs


class BookingRescheduleRequestSerializer(serializers.Serializer):
    """
    Serializer for reschedule request.
    """

    new_date = serializers.DateField()
    new_time = serializers.TimeField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class BookingListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for booking lists.
    """

    client_name = serializers.CharField(source='client.name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'client_name', 'package_name', 'event_date', 'event_time',
            'venue', 'pax_count', 'status', 'total_amount'
        ]


class CalendarEventSerializer(serializers.Serializer):
    """
    Serializer for calendar events.
    """

    id = serializers.IntegerField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    client_name = serializers.CharField()
    venue = serializers.CharField()
    pax_count = serializers.IntegerField()
    color = serializers.CharField()
