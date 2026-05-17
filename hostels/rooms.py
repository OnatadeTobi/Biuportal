from hostels.models import Room
from hostels.utils import canonicalize_hostel, hostels_match, normalize_hostel_for_storage


def find_or_create_room(hostel: str, room_number: str):
    """
    Find an existing room (case-insensitive hostel match) or create one.
    Returns (room, created).
    """
    room_number = room_number.strip()
    hostel_canonical = canonicalize_hostel(hostel)

    for room in Room.objects.filter(room_number=room_number):
        if hostels_match(room.hostel, hostel_canonical):
            return room, False

    room = Room.objects.create(hostel=hostel_canonical, room_number=room_number)
    return room, True
