import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from accounts.models import EmailVerificationOTP


def generate_otp_code():
    return f'{secrets.randbelow(1_000_000):06d}'


def hash_otp(otp_code):
    return hashlib.sha256(otp_code.encode('utf-8')).hexdigest()


def create_otp_for_user(user):
    otp_code = generate_otp_code()
    expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    EmailVerificationOTP.objects.create(
        user=user,
        otp_hash=hash_otp(otp_code),
        expires_at=expires_at,
    )
    return otp_code


def verify_otp(user, otp_code):
    otp_hash = hash_otp(otp_code.strip())
    otp_record = (
        EmailVerificationOTP.objects.filter(
            user=user,
            otp_hash=otp_hash,
            is_used=False,
        )
        .order_by('-created_at')
        .first()
    )
    if not otp_record:
        return 'invalid'
    if otp_record.expires_at < timezone.now():
        return 'expired'
    otp_record.is_used = True
    otp_record.save(update_fields=['is_used'])
    return 'valid'
