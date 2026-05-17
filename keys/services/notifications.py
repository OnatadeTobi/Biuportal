from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


def _format_time(dt):
    local = timezone.localtime(dt)
    return local.strftime('%I:%M %p').lstrip('0')


def notify_room_students(room, actor, action_type, resulting_status, event_time):
    """Email all verified, active students registered in the same room."""
    profiles = room.students.select_related('user').filter(
        user__is_email_verified=True,
        user__is_active=True,
    )
    recipients = [p.user.email for p in profiles if p.user.email]
    if not recipients:
        return

    hostel_name = room.hostel
    room_number = room.room_number
    time_str = _format_time(event_time)

    if action_type == 'DROP':
        subject = f'{hostel_name} Room {room_number} Key Dropped'
        status_line = 'At Porter'
        verb = 'dropped'
        location = "at the porter's lodge"
    else:
        subject = f'{hostel_name} Room {room_number} Key Collected'
        status_line = 'With Student'
        verb = 'collected'
        location = "from the porter's lodge"

    body = (
        f'{actor.full_name} {verb} the Room {room_number} key {location}.\n\n'
        f'Hostel: {hostel_name}\n'
        f'Room: {room_number}\n'
        f'Status: {status_line}\n'
        f'Time: {time_str}\n'
    )

    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )
