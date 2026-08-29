"""
Twilio SMS sending for reminders.
"""

from django.conf import settings


def twilio_is_configured():
    """
    Return whether Twilio credentials are present.
    """
    return bool(
        getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        and getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        and getattr(settings, 'TWILIO_FROM_NUMBER', '')
    )


def get_twilio_client():
    """
    Build a Twilio REST client from settings.
    """
    from twilio.rest import Client

    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_sms_reminder(reminder):
    """
    Send an SMS via Twilio. Return False when SMS is not configured.
    """
    if not twilio_is_configured():
        return False
    if not reminder.recipient_phone:
        raise ValueError('SMS reminder is missing a recipient phone number')

    get_twilio_client().messages.create(
        body=reminder.message,
        from_=settings.TWILIO_FROM_NUMBER,
        to=reminder.recipient_phone,
    )
    return True
