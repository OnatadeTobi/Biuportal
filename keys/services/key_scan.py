from django.db import transaction
from django.utils import timezone

from hostels.utils import hostels_match
from keys.models import KeyActivity, KeyStatus, QRCode
from keys.services.notifications import notify_room_students


class KeyScanError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def get_or_create_key_status(room):
    key_status, _ = KeyStatus.objects.get_or_create(
        room=room,
        defaults={'status': KeyStatus.Status.AT_PORTER},
    )
    return key_status


def process_qr_scan(user, qr_code_id):
    """
    Process a QR scan for the authenticated student's room.

    Returns dict with success data or raises KeyScanError.
    """
    try:
        qr_code = QRCode.objects.get(qr_code_id=qr_code_id)
    except QRCode.DoesNotExist:
        raise KeyScanError('Invalid or inactive QR code.')

    if not qr_code.is_active:
        raise KeyScanError('Invalid or inactive QR code.')

    profile = user.profile
    room = profile.room

    if not hostels_match(qr_code.hostel, room.hostel):
        raise KeyScanError('This QR code does not belong to your hostel.')

    key_status = get_or_create_key_status(room)
    action_type = qr_code.action_type
    current = key_status.status

    if action_type == QRCode.ActionType.COLLECT:
        if current == KeyStatus.Status.WITH_STUDENT:
            raise KeyScanError('This key has already been collected.')
        if current != KeyStatus.Status.AT_PORTER:
            raise KeyScanError('This key has already been collected.')
        new_status = KeyStatus.Status.WITH_STUDENT
        success_message = 'Key collected successfully.'
    elif action_type == QRCode.ActionType.DROP:
        if current == KeyStatus.Status.AT_PORTER:
            raise KeyScanError("This key is already at the porter's lodge.")
        if current != KeyStatus.Status.WITH_STUDENT:
            raise KeyScanError("This key is already at the porter's lodge.")
        new_status = KeyStatus.Status.AT_PORTER
        success_message = 'Key dropped successfully.'
    else:
        raise KeyScanError('Invalid or inactive QR code.')

    now = timezone.now()

    with transaction.atomic():
        key_status.status = new_status
        key_status.last_action_by = user
        key_status.last_updated = now
        key_status.save(update_fields=['status', 'last_action_by', 'last_updated'])

        KeyActivity.objects.create(
            room=room,
            student=user,
            qr_code=qr_code,
            action_type=action_type,
            resulting_status=new_status,
            timestamp=now,
        )

    notify_room_students(room, user, action_type, new_status, now)

    return {
        'success': True,
        'message': success_message,
        'action_type': action_type,
        'key_status': new_status,
        'student': user.full_name,
        'hostel': room.hostel,
        'room_number': room.room_number,
        'timestamp': now.isoformat(),
    }
