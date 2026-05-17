from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from accounts.models import User
from accounts.services.email import send_verification_otp_email
from accounts.services.otp import create_otp_for_user, verify_otp
from accounts.services.student_lookup import fetch_student_by_matric
from hostels.rooms import find_or_create_room
from keys.services.key_scan import get_or_create_key_status


class LookupStudentSerializer(serializers.Serializer):
    matric_number = serializers.CharField(max_length=50)

    def validate_matric_number(self, value):
        student = fetch_student_by_matric(value)
        if not student:
            raise serializers.ValidationError('Student record not found.')
        self.context['student_data'] = student
        return value.strip()


class RegisterSerializer(serializers.Serializer):
    matric_number = serializers.CharField(max_length=50)
    hostel = serializers.CharField(max_length=100)
    room_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        validate_password(attrs['password'])
        attrs['hostel'] = attrs['hostel'].strip()
        attrs['room_number'] = attrs['room_number'].strip()
        if not attrs['hostel']:
            raise serializers.ValidationError({'hostel': 'Hostel is required.'})
        if not attrs['room_number']:
            raise serializers.ValidationError({'room_number': 'Room number is required.'})
        return attrs

    def validate_matric_number(self, value):
        matric = value.strip()
        student = fetch_student_by_matric(matric)
        if not student:
            raise serializers.ValidationError('Student record not found.')
        if User.objects.filter(matric_number=matric).exists():
            raise serializers.ValidationError('An account already exists for this matric number.')
        if User.objects.filter(email=student['email']).exists():
            raise serializers.ValidationError('An account already exists for this email.')
        self.context['student_data'] = student
        return matric

    @transaction.atomic
    def create(self, validated_data):
        student = self.context['student_data']
        room, _ = find_or_create_room(
            validated_data['hostel'],
            validated_data['room_number'],
        )

        user = User.objects.create_user(
            email=student['email'],
            matric_number=student['matric_number'],
            full_name=student['full_name'],
            password=validated_data['password'],
            is_active=False,
            is_email_verified=False,
        )

        from accounts.models import StudentProfile

        StudentProfile.objects.create(user=user, room=room)
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
