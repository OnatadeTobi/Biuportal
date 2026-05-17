def build_user_profile_dict(user):
    profile = getattr(user, 'profile', None)
    hostel_name = ''
    room_number = ''
    if profile and profile.room:
        hostel_name = profile.room.hostel
        room_number = profile.room.room_number
    return {
        'full_name': user.full_name,
        'email': user.email,
        'matric_number': user.matric_number,
        'hostel': hostel_name,
        'room_number': room_number,
    }
