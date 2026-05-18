from hostels.models import Room
from hostels.utils import normalize_location


def find_or_create_room(hostel: str, room_number: str):
    """
    Find or create a shared room by hostel + room number (case-insensitive match).
    Returns (room, created).
    """
    hostel_stored = normalize_location(hostel)
    room_number = room_number.strip()

    for room in Room.objects.filter(room_number__iexact=room_number):
        if normalize_location(room.hostel).casefold() == hostel_stored.casefold():
            return room, False

    room = Room.objects.create(hostel=hostel_stored, room_number=room_number)
    return room, True
