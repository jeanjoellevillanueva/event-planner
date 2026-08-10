"""
Celery tasks for reminders app.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone


@shared_task(bind=True, max_retries=3)
def send_reminder(self, reminder_id):
    """
    Send a scheduled reminder.
    """
    from apps.reminders.models import Reminder

    try:
        reminder = Reminder.objects.select_related(
            'booking', 'booking__client', 'booking__business'
        ).get(pk=reminder_id)
    except Reminder.DoesNotExist:
        return f"Reminder {reminder_id} not found"

    if not reminder.can_send:
        return f"Reminder {reminder_id} cannot be sent (status: {reminder.status})"

    try:
        if reminder.reminder_type == 'email':
            send_email_reminder(reminder)
        elif reminder.reminder_type == 'sms':
            send_sms_reminder(reminder)

        reminder.mark_sent()
        return f"Reminder {reminder_id} sent successfully"

    except Exception as exc:
        reminder.mark_failed(str(exc))

        if reminder.retry_count < 3:
            raise self.retry(exc=exc, countdown=60 * (2 ** reminder.retry_count))

        return f"Reminder {reminder_id} failed: {exc}"


def send_email_reminder(reminder):
    """
    Send email reminder.
    """
    business = reminder.booking.business

    send_mail(
        subject=reminder.subject or f"Reminder from {business.name}",
        message=reminder.message,
        from_email=None,
        recipient_list=[reminder.recipient_email],
        fail_silently=False,
    )


def send_sms_reminder(reminder):
    """
    Send SMS reminder (placeholder for Twilio integration).
    """
    pass


@shared_task
def process_pending_reminders():
    """
    Process all pending reminders that are due.
    """
    from apps.reminders.models import Reminder

    now = timezone.now()

    pending_reminders = Reminder.objects.filter(
        status='pending',
        scheduled_at__lte=now
    ).values_list('id', flat=True)

    for reminder_id in pending_reminders:
        send_reminder.delay(reminder_id)

    return f"Queued {len(pending_reminders)} reminders for sending"


@shared_task
def create_event_reminders():
    """
    Auto-create reminders for upcoming events.
    """
    from datetime import timedelta
    from apps.bookings.models import Booking
    from apps.reminders.models import Reminder
    from apps.reminders.models import ReminderTemplate

    now = timezone.now()
    three_days_ahead = now.date() + timedelta(days=3)
    one_day_ahead = now.date() + timedelta(days=1)

    upcoming_bookings = Booking.objects.filter(
        status='confirmed',
        event_date__in=[three_days_ahead, one_day_ahead]
    ).select_related('client', 'business')

    reminders_created = 0

    for booking in upcoming_bookings:
        existing = Reminder.objects.filter(
            booking=booking,
            scheduled_at__date=now.date(),
            status='pending'
        ).exists()

        if existing:
            continue

        template = ReminderTemplate.objects.filter(
            business=booking.business,
            template_type='event_reminder',
            is_active=True
        ).first()

        if not booking.client.email:
            continue

        subject = f"Reminder: Your event on {booking.event_date.strftime('%B %d, %Y')}"
        message = f"This is a reminder for your upcoming event."

        if template:
            subject, message = template.render(booking)

        Reminder.objects.create(
            booking=booking,
            reminder_type='email',
            scheduled_at=now,
            subject=subject,
            message=message,
            recipient_email=booking.client.email
        )

        reminders_created += 1

    return f"Created {reminders_created} event reminders"
