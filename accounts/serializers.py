from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from accounts.models import User
from accounts.services.email import send_verification_otp_email
from accounts.services.otp import create_otp_for_user, verify_otp
from hostels.rooms import find_or_create_room
from keys.services.key_scan import get_or_create_key_status

MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_PROFILE_PICTURE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}


class RegisterSerializer(serializers.Serializer):
    matric_number = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    hostel = serializers.CharField(max_length=100)
    room_number = serializers.CharField(max_length=20)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    flat_number = serializers.CharField(max_length=20)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_profile_picture(self, value):
        if value is None:
            return value
        if value.size > MAX_PROFILE_PICTURE_SIZE:
            raise serializers.ValidationError('Profile picture must be 5 MB or smaller.')
        content_type = getattr(value, 'content_type', '')
        if content_type and content_type not in ALLOWED_PROFILE_PICTURE_TYPES:
            raise serializers.ValidationError('Profile picture must be JPEG, PNG, or WebP.')
        return value

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('An account already exists for this email.')
        return email

    def validate_matric_number(self, value):
        matric = value.strip()
        if User.objects.filter(matric_number=matric).exists():
            raise serializers.ValidationError('An account already exists for this matric number.')
        return matric

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        validate_password(attrs['password'])
        attrs['hostel'] = attrs['hostel'].strip()
        attrs['room_number'] = attrs['room_number'].strip()
        attrs['first_name'] = attrs['first_name'].strip()
        attrs['last_name'] = attrs['last_name'].strip()
        attrs['flat_number'] = attrs['flat_number'].strip()
        if not attrs['hostel']:
            raise serializers.ValidationError({'hostel': 'Hostel is required.'})
        if not attrs['room_number']:
            raise serializers.ValidationError({'room_number': 'Room number is required.'})
        if not attrs['first_name']:
            raise serializers.ValidationError({'first_name': 'First name is required.'})
        if not attrs['last_name']:
            raise serializers.ValidationError({'last_name': 'Last name is required.'})
        if not attrs['flat_number']:
            raise serializers.ValidationError({'flat_number': 'Flat number is required.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_picture = validated_data.pop('profile_picture', None)
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')

        room, _ = find_or_create_room(
            validated_data['hostel'],
            validated_data['room_number'],
        )

        full_name = f"{validated_data['first_name']} {validated_data['last_name']}".strip()

        user = User.objects.create_user(
            email=validated_data['email'],
            matric_number=validated_data['matric_number'],
            full_name=full_name,
            password=password,
            is_active=False,
            is_email_verified=False,
        )

        from accounts.models import StudentProfile

        StudentProfile.objects.create(
            user=user,
            room=room,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            flat_number=validated_data['flat_number'],
            profile_picture=profile_picture,
        )
        get_or_create_key_status(room)

        otp_code = create_otp_for_user(user)
        send_verification_otp_email(user, otp_code)
        return user


class VerifyEmailSerializer(serializers.Serializer):
    matric_number = serializers.CharField(max_length=50)
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        matric = attrs['matric_number'].strip()
        try:
            user = User.objects.get(matric_number=matric)
        except User.DoesNotExist:
            raise serializers.ValidationError({'matric_number': 'Account not found.'})

        if user.is_email_verified:
            raise serializers.ValidationError('Email is already verified.')

        result = verify_otp(user, attrs['otp'])
        if result == 'invalid':
            raise serializers.ValidationError({'otp': 'Invalid verification code.'})
        if result == 'expired':
            raise serializers.ValidationError(
                {'otp': 'Verification code has expired. Please request a new one.'}
            )

        user.is_email_verified = True
        user.is_active = True
        user.save(update_fields=['is_email_verified', 'is_active'])
        attrs['user'] = user
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    matric_number = serializers.CharField(max_length=50)

    def validate_matric_number(self, value):
        matric = value.strip()
        try:
            user = User.objects.get(matric_number=matric)
        except User.DoesNotExist:
            raise serializers.ValidationError('Account not found.')
        if user.is_email_verified:
            raise serializers.ValidationError(
                'Email is already verified.',
                code='already_verified',
            )
        self.context['user'] = user
        return matric


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs['identifier'].strip()
        password = attrs['password']

        user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            user = User.objects.filter(matric_number=identifier).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials.')

        if not user.is_email_verified:
            raise serializers.ValidationError('Please verify your email before logging in.')

        if not user.is_active:
            raise serializers.ValidationError('Account is inactive.')

        attrs['user'] = user
        return attrs
