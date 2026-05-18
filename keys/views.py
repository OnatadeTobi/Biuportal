from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsEmailVerified
from accounts.utils import build_user_profile_dict
from keys.models import KeyActivity, QRCode
from keys.serializers import ScanQRSerializer
from keys.services.key_scan import KeyScanError, get_or_create_key_status, process_qr_scan
from keys.utils import build_activity_dict, build_key_status_dict, build_key_status_with_room_dict


class DashboardView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        profile = request.user.profile
        room = profile.room
        key_status = getattr(room, 'key_status', None)
        if key_status is None:
            key_status = get_or_create_key_status(room)

        activities = KeyActivity.objects.filter(room=room).select_related('student', 'room')[:10]

        user_summary = build_user_profile_dict(request.user, request)

        recent = [
            {
                'action_type': a.action_type,
                'label': build_activity_dict(a)['label'],
                'student': a.student.full_name,
                'timestamp': a.timestamp.isoformat(),
                'resulting_status': a.resulting_status,
            }
            for a in activities
        ]

        return Response({
            'success': True,
            'user': user_summary,
            'key_status': build_key_status_dict(room, key_status),
            'recent_activity': recent,
        })


class KeyStatusView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        room = request.user.profile.room
        return Response({
            'success': True,
            'key_status': build_key_status_with_room_dict(room),
        })


class KeyActivityView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request):
        room = request.user.profile.room
        activities = KeyActivity.objects.filter(room=room).select_related('student', 'room')
        return Response({
            'success': True,
            'activities': [build_activity_dict(a) for a in activities],
        })


class ScanQRView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request):
        serializer = ScanQRSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'message': 'Invalid request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = process_qr_scan(request.user, serializer.validated_data['qr_code_id'])
        except KeyScanError as exc:
            return Response({'success': False, 'message': exc.message}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class QRCodeSetupView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qr_codes = QRCode.objects.order_by('hostel', 'action_type')
        data = [
            {
                'hostel': qr.hostel,
                'action_type': qr.action_type,
                'qr_code_id': qr.qr_code_id,
                'is_active': qr.is_active,
            }
            for qr in qr_codes
        ]
        return Response({'success': True, 'qr_codes': data})
