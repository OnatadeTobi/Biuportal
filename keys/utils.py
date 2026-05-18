from keys.constants import ACTION_LABELS, KEY_STATUS_LABELS
from keys.services.key_scan import get_or_create_key_status


def build_key_status_dict(room, key_status=None):
    if key_status is None:
        key_status = get_or_create_key_status(room)
    last_by = ''
    if key_status.last_action_by:
        last_by = key_status.last_action_by.full_name
    return {
        'status': key_status.status,
        'label': KEY_STATUS_LABELS.get(key_status.status, key_status.status),
        'last_updated': key_status.last_updated.isoformat(),
        'last_action_by': last_by,
    }


def build_key_status_with_room_dict(room, key_status=None):
    data = build_key_status_dict(room, key_status)
    data['hostel'] = room.hostel
    data['room_number'] = room.room_number
    return data


def build_activity_dict(activity):
    return {
        'action_type': activity.action_type,
        'label': ACTION_LABELS.get(activity.action_type, activity.action_type),
        'student': activity.student.full_name,
        'hostel': activity.room.hostel,
        'room_number': activity.room.room_number,
        'flat_number': activity.flat_number,
        'timestamp': activity.timestamp.isoformat(),
        'resulting_status': activity.resulting_status,
    }
