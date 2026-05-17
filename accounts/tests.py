from django.test import TestCase
from rest_framework.test import APIClient

from hostels.utils import hostels_match
from keys.models import KeyStatus, QRCode


class AuthAndKeyFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.core.management import call_command
        call_command('seed_mvp_data')

    def test_full_registration_and_scan_flow(self):
        matric = 'BIU/23/CSC/001'
        hostel_name = 'Hope Hostel'

        r = self.client.post('/api/auth/lookup-student/', {'matric_number': matric}, format='json')
        self.assertTrue(r.data['success'])

        r = self.client.post('/api/auth/register/', {
            'matric_number': matric,
            'hostel': hostel_name,
            'room_number': '14',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }, format='json')
        self.assertTrue(r.data['success'])

        from accounts.models import EmailVerificationOTP, User
        from accounts.services.otp import generate_otp_code, hash_otp

        user = User.objects.get(matric_number=matric)
        otp_code = generate_otp_code()
        EmailVerificationOTP.objects.create(
            user=user,
            otp_hash=hash_otp(otp_code),
            expires_at=user.otps.first().expires_at,
            is_used=False,
        )

        r = self.client.post('/api/auth/verify-email/', {
            'matric_number': matric,
            'otp': otp_code,
        }, format='json')
        self.assertTrue(r.data['success'])

        r = self.client.post('/api/auth/login/', {
            'identifier': matric,
            'password': 'Password123!',
        }, format='json')
        self.assertTrue(r.data['success'])
        self.assertEqual(r.data['user']['hostel'], hostel_name)
        token = r.data['token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        collect_qr = QRCode.objects.get(hostel=hostel_name, action_type='COLLECT').qr_code_id
        r = self.client.post('/api/keys/scan/', {'qr_code_id': collect_qr}, format='json')
        self.assertTrue(r.data['success'])
        self.assertEqual(r.data['key_status'], KeyStatus.Status.WITH_STUDENT)

        r = self.client.post('/api/keys/scan/', {'qr_code_id': collect_qr}, format='json')
        self.assertFalse(r.data['success'])

        drop_qr = QRCode.objects.get(hostel=hostel_name, action_type='DROP').qr_code_id
        r = self.client.post('/api/keys/scan/', {'qr_code_id': drop_qr}, format='json')
        self.assertTrue(r.data['success'])
        self.assertEqual(r.data['key_status'], KeyStatus.Status.AT_PORTER)

    def test_hostel_case_insensitive_scan(self):
        matric = 'BIU/23/CSC/002'
        r = self.client.post('/api/auth/register/', {
            'matric_number': matric,
            'hostel': 'hope hostel',
            'room_number': '20',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }, format='json')
        self.assertTrue(r.data['success'])

        from accounts.models import EmailVerificationOTP, User
        from accounts.services.otp import generate_otp_code, hash_otp

        user = User.objects.get(matric_number=matric)
        otp_code = generate_otp_code()
        EmailVerificationOTP.objects.create(
            user=user,
            otp_hash=hash_otp(otp_code),
            expires_at=user.otps.first().expires_at,
            is_used=False,
        )
        self.client.post('/api/auth/verify-email/', {'matric_number': matric, 'otp': otp_code}, format='json')
        r = self.client.post('/api/auth/login/', {
            'identifier': matric,
            'password': 'Password123!',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["token"]}')

        collect_qr = QRCode.objects.get(hostel='Hope Hostel', action_type='COLLECT').qr_code_id
        r = self.client.post('/api/keys/scan/', {'qr_code_id': collect_qr}, format='json')
        self.assertTrue(r.data['success'])
        self.assertTrue(hostels_match(user.profile.room.hostel, 'Hope Hostel'))

    def test_wrong_hostel_qr_rejected(self):
        matric = 'BIU/23/CSC/003'
        self.client.post('/api/auth/register/', {
            'matric_number': matric,
            'hostel': 'Peace Hostel',
            'room_number': '5',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }, format='json')

        from accounts.models import EmailVerificationOTP, User
        from accounts.services.otp import generate_otp_code, hash_otp

        user = User.objects.get(matric_number=matric)
        otp_code = generate_otp_code()
        EmailVerificationOTP.objects.create(
            user=user,
            otp_hash=hash_otp(otp_code),
            expires_at=user.otps.first().expires_at,
            is_used=False,
        )
        self.client.post('/api/auth/verify-email/', {'matric_number': matric, 'otp': otp_code}, format='json')
        r = self.client.post('/api/auth/login/', {
            'identifier': matric,
            'password': 'Password123!',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["token"]}')

        hope_collect = QRCode.objects.get(hostel='Hope Hostel', action_type='COLLECT').qr_code_id
        r = self.client.post('/api/keys/scan/', {'qr_code_id': hope_collect}, format='json')
        self.assertFalse(r.data['success'])
        self.assertEqual(r.data['message'], 'This QR code does not belong to your hostel.')

    def test_invalid_matric_lookup(self):
        r = self.client.post('/api/auth/lookup-student/', {'matric_number': 'INVALID'}, format='json')
        self.assertFalse(r.data['success'])
        self.assertEqual(r.data['message'], 'Student record not found.')

    def test_hostels_endpoint_removed(self):
        r = self.client.get('/api/hostels/')
        self.assertEqual(r.status_code, 404)
