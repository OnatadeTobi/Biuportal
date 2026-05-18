def _profile_picture_url(profile, request=None):
    if not profile or not profile.profile_picture:
        return None
    url = profile.profile_picture.url
    if request:
        return request.build_absolute_uri(url)
    return url


def build_user_profile_dict(user, request=None):
    profile = getattr(user, 'profile', None)
    hostel_name = ''
    room_number = ''
    first_name = ''
    last_name = ''
    flat_number = ''
    profile_picture = None

    if profile:
        first_name = profile.first_name
        last_name = profile.last_name
        flat_number = profile.flat_number
        profile_picture = _profile_picture_url(profile, request)
        if profile.room:
            hostel_name = profile.room.hostel
            room_number = profile.room.room_number

    return {
        'full_name': user.full_name,
        'first_name': first_name,
        'last_name': last_name,
        'email': user.email,
        'matric_number': user.matric_number,
        'hostel': hostel_name,
        'room_number': room_number,
        'flat_number': flat_number,
        'profile_picture': profile_picture,
    }
