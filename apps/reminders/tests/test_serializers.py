"""
Tests for reminders serializers.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.reminders.models import Reminder
from apps.reminders.models import ReminderTemplate
from apps.reminders.serializers import ReminderCreateSerializer
from apps.reminders.serializers import ReminderSerializer
from apps.reminders.serializers import ReminderTemplateCreateSerializer
from apps.reminders.serializers import ReminderTemplateSerializer


@pytest.mark.django_db
class TestReminderSerializer:
    """
    Tests for ReminderSerializer.
    """

    def test_serialize_reminder(self, booking_factory):
        """
        Should serialize reminder with related info.
        """
        booking = booking_factory()
        reminder = Reminder.objects.create(
            booking=booking,
            reminder_type='email',
            scheduled_at=timezone.now() + timedelta(days=1),
            subject='Test Reminder',
            message='Test message',
            recipient_email='test@example.com'
        )

        serializer = ReminderSerializer(reminder)
        data = serializer.data

        assert data['reminder_type'] == 'email'
        assert data['subject'] == 'Test Reminder'
        assert 'client_name' in data
        assert 'event_date' in data


@pytest.mark.django_db
class TestReminderCreateSerializer:
    """
    Tests for ReminderCreateSerializer.
    """

    def test_valid_email_reminder(self, authenticated_client, booking_factory):
        """
        Should validate email reminder with recipient.
        """
        booking = booking_factory(business=authenticated_client.business)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'booking': booking.id,
            'reminder_type': 'email',
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'subject': 'Reminder',
            'message': 'Your event is coming up!',
            'recipient_email': 'client@example.com',
        }
        serializer = ReminderCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_email_reminder_uses_client_email(self, authenticated_client, booking_factory, client_factory):
        """
        Should use client email if not provided.
        """
        client = client_factory(business=authenticated_client.business, email='client@test.com')
        booking = booking_factory(business=authenticated_client.business, client=client)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'booking': booking.id,
            'reminder_type': 'email',
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'subject': 'Reminder',
            'message': 'Your event is coming up!',
        }
        serializer = ReminderCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['recipient_email'] == 'client@test.com'

    def test_sms_reminder_uses_client_phone(self, authenticated_client, booking_factory, client_factory):
        """
        Should use client phone for SMS if not provided.
        """
        client = client_factory(business=authenticated_client.business, phone='1234567890')
        booking = booking_factory(business=authenticated_client.business, client=client)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'booking': booking.id,
            'reminder_type': 'sms',
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'message': 'Reminder!',
        }
        serializer = ReminderCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['recipient_phone'] == '1234567890'

    def test_booking_from_other_business_rejected(self, authenticated_client, business_factory, booking_factory):
        """
        Should reject booking from different business.
        """
        other_business = business_factory(name='Other')
        other_booking = booking_factory(business=other_business)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'booking': other_booking.id,
            'reminder_type': 'email',
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'message': 'Test',
            'recipient_email': 'test@example.com',
        }
        serializer = ReminderCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'booking' in serializer.errors

    def test_with_valid_template(self, authenticated_client, booking_factory):
        """
        Should apply template content.
        """
        booking = booking_factory(business=authenticated_client.business)
        template = ReminderTemplate.objects.create(
            business=authenticated_client.business,
            name='Event Reminder',
            template_type='event_reminder',
            subject='Reminder: {{event_date}}',
            content='Hello {{client_name}}, your event is coming!'
        )

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'booking': booking.id,
            'reminder_type': 'email',
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'message': 'Placeholder',
            'recipient_email': 'test@example.com',
            'template_id': template.id,
        }
        serializer = ReminderCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), serializer.errors

    def test_invalid_template_id_rejected(self, authenticated_client, booking_factory):
        """
        Should reject invalid template_id.
        """
        booking = booking_factory(business=authenticated_client.business)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = authenticated_client.user

        data = {
            'booking': booking.id,
            'reminder_type': 'email',
            'scheduled_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'message': 'Test',
            'recipient_email': 'test@example.com',
            'template_id': 99999,
        }
        serializer = ReminderCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with pytest.raises(Exception):
            serializer.save()


@pytest.mark.django_db
class TestReminderTemplateSerializer:
    """
    Tests for ReminderTemplateSerializer.
    """

    def test_serialize_template(self, business_factory):
        """
        Should serialize template with all fields.
        """
        business = business_factory()
        template = ReminderTemplate.objects.create(
            business=business,
            name='Payment Reminder',
            template_type='payment_reminder',
            subject='Payment Due',
            content='Please pay {{balance_amount}}'
        )

        serializer = ReminderTemplateSerializer(template)
        data = serializer.data

        assert data['name'] == 'Payment Reminder'
        assert data['template_type'] == 'payment_reminder'


class TestReminderTemplateCreateSerializer:
    """
    Tests for ReminderTemplateCreateSerializer.
    """

    def test_valid_template_creation(self):
        """
        Should validate correct template data.
        """
        data = {
            'name': 'New Template',
            'template_type': 'event_reminder',
            'subject': 'Reminder',
            'content': 'Your event is on {{event_date}}',
        }
        serializer = ReminderTemplateCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_template_type(self):
        """
        Should reject invalid template type.
        """
        data = {
            'name': 'Bad Template',
            'template_type': 'invalid_type',
            'content': 'Content',
        }
        serializer = ReminderTemplateCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'template_type' in serializer.errors
