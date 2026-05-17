from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.permissions import IsEmailVerified
from accounts.serializers import (
    LoginSerializer,
    LookupStudentSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    VerifyEmailSerializer,
)
from accounts.services.email import send_verification_otp_email
from accounts.services.otp import create_otp_for_user
from accounts.utils import build_user_profile_dict


class LookupStudentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LookupStudentSerializer(data=request.data)
        if not serializer.is_valid():
            message = serializer.errors.get('matric_number', ['Invalid request.'])[0]
            if isinstance(message, list):
                message = message[0]
            return Response({'success': False, 'message': str(message)}, status=status.HTTP_400_BAD_REQUEST)
        student = serializer.context['student_data']
        return Response({'success': True, 'student': student})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            for field in ('matric_number', 'non_field_errors'):
                if field in errors:
                    msg = errors[field]
                    message = msg[0] if isinstance(msg, list) else msg
                    return Response({'success': False, 'message': str(message)}, status=status.HTTP_400_BAD_REQUEST)
            first_error = next(iter(errors.values()))
            message = first_error[0] if isinstance(first_error, list) else first_error
            return Response({'success': False, 'message': str(message)}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({
            'success': True,
            'message': 'Account created. Verification code sent to your email.',
        })


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if not serializer.is_valid():
            if 'otp' in serializer.errors:
                message = serializer.errors['otp'][0]
            elif 'matric_number' in serializer.errors:
                message = serializer.errors['matric_number'][0]
            else:
                message = next(iter(serializer.errors.values()))[0]
            return Response({'success': False, 'message': str(message)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, 'message': 'Email verified successfully.'})


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            if 'non_field_errors' in errors:
                message = errors['non_field_errors'][0]
            elif 'matric_number' in errors:
                message = errors['matric_number'][0]
            else:
                message = 'Invalid request.'
            return Response({'success': False, 'message': str(message)}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.context['user']
        otp_code = create_otp_for_user(user)
        send_verification_otp_email(user, otp_code)
        return Response({
            'success': True,
            'message': 'A new verification code has been sent to your email.',
        })


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            if 'non_field_errors' in errors:
                message = errors['non_field_errors'][0]
            else:
                message = 'Invalid credentials.'
            return Response({'success': False, 'message': str(message)}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'token': str(refresh.access_token),
            'user': build_user_profile_dict(user),
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        user_data = build_user_profile_dict(request.user)
        user_data['is_email_verified'] = request.user.is_email_verified
        return Response({'success': True, 'user': user_data})
