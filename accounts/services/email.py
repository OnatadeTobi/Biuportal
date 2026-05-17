from django.conf import settings
from django.core.mail import send_mail


def send_verification_otp_email(user, otp_code):
    subject = 'BIU Hostel Key Portal - Email Verification Code'
    message = (
        f'Hello {user.full_name},\n\n'
        f'Your email verification code is: {otp_code}\n\n'
        f'This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n\n'
        f'If you did not request this, please ignore this email.\n'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
