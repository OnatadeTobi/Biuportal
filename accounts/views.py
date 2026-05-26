from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsEmailVerified
from accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    VerifyEmailSerializer,
)
from accounts.services.student_lookup import BIUPortalError, fetch_biu_student_details
from accounts.services.email import send_verification_otp_email
from accounts.services.otp import create_otp_for_user
from accounts.utils import build_user_profile_dict
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = RegisterSerializer

    @extend_schema(responses={201: RegisterSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
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
    serializer_class = VerifyEmailSerializer

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
    serializer_class = ResendOTPSerializer

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
    serializer_class = LoginSerializer

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
            'user': build_user_profile_dict(user, request),
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    @extend_schema(responses={200: None})  # We could define a dedicated serializer for the response if needed
    def get(self, request):
        user_data = build_user_profile_dict(request.user, request)
        user_data['is_email_verified'] = request.user.is_email_verified
        return Response({'success': True, 'user': user_data})


class StudentLookupView(APIView):
    """
    Look up student details from the external BIU portal.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: None})
    def get(self, request):
        matric_no = request.query_params.get('matric_no', '').strip()

        if not matric_no:
            return Response(
                {'success': False, 'message': 'matric_no query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Basic validation for matric_no: allow letters, numbers, /, -, _
        import re
        if not re.match(r'^[A-Za-z0-9/_-]+$', matric_no):
            return Response(
                {'success': False, 'message': 'Invalid matric_no format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reject full URLs
        if '://' in matric_no:
            return Response(
                {'success': False, 'message': 'Invalid matric_no format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student_data = fetch_biu_student_details(matric_no)
            return Response({
                'success': True,
                'source': 'biu_portal',
                'matric_no': matric_no,
                'data': student_data
            })
        except BIUPortalError as e:
            return Response(
                {'success': False, 'message': e.message},
                status=e.status_code
            )
        except Exception:
            # Safe 500 response for unexpected parsing or internal errors
            return Response(
                {'success': False, 'message': 'An unexpected error occurred while fetching student data.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
