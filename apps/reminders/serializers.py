"""
Serializers for reminders app.
"""

from rest_framework import serializers

from apps.common.mixins import TimezoneAwareMixin
from apps.reminders.models import Reminder
from apps.reminders.models import ReminderTemplate


class ReminderSerializer(TimezoneAwareMixin, serializers.ModelSerializer):
    """
    Serializer for Reminder model.
    """

    booking_id = serializers.IntegerField(source='booking.id', read_only=True)
    client_name = serializers.CharField(source='booking.client.name', read_only=True)
    event_date = serializers.DateField(source='booking.event_date', read_only=True)

    class Meta:
        model = Reminder
        fields = [
            'id', 'booking', 'booking_id', 'client_name', 'event_date',
            'reminder_type', 'scheduled_at', 'sent_at', 'status',
            'subject', 'message', 'recipient_email', 'recipient_phone',
            'error_message', 'retry_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sent_at', 'status', 'error_message', 'retry_count', 'created_at', 'updated_at']


class ReminderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reminders.
    """

    template_id = serializers.IntegerField(required=False)

    class Meta:
        model = Reminder
        fields = [
            'booking', 'reminder_type', 'scheduled_at',
            'subject', 'message', 'recipient_email', 'recipient_phone',
            'template_id'
        ]

    def validate_booking(self, value):
        """
        Ensure booking belongs to user's business.
        """
        business = self.context['request'].user.current_business
        if value.business != business:
            raise serializers.ValidationError("Booking does not belong to your business")
        return value

    def validate(self, attrs):
        """
        Validate recipient based on reminder type.
        """
        reminder_type = attrs.get('reminder_type')
        if reminder_type == 'email' and not attrs.get('recipient_email'):
            booking = attrs.get('booking')
            if booking and booking.client.email:
                attrs['recipient_email'] = booking.client.email
            else:
                raise serializers.ValidationError({
                    'recipient_email': 'Email is required for email reminders'
                })

        if reminder_type == 'sms' and not attrs.get('recipient_phone'):
            booking = attrs.get('booking')
            if booking and booking.client.phone:
                attrs['recipient_phone'] = booking.client.phone
            else:
                raise serializers.ValidationError({
                    'recipient_phone': 'Phone is required for SMS reminders'
                })

        return attrs

    def create(self, validated_data):
        """
        Create reminder, optionally using template.
        """
        template_id = validated_data.pop('template_id', None)

        if template_id:
            try:
                template = ReminderTemplate.objects.get(
                    pk=template_id,
                    business=validated_data['booking'].business,
                    is_active=True
                )
                subject, message = template.render(validated_data['booking'])
                validated_data['subject'] = subject
                validated_data['message'] = message
            except ReminderTemplate.DoesNotExist:
                raise serializers.ValidationError({
                    'template_id': 'Template not found or inactive'
                })

        return super().create(validated_data)


class ReminderTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for ReminderTemplate model.
    """

    class Meta:
        model = ReminderTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'content',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReminderTemplateCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating reminder templates.
    """

    class Meta:
        model = ReminderTemplate
        fields = ['name', 'template_type', 'subject', 'content']
