from django.test import TestCase
from rest_framework.test import APIClient

from hostels.utils import hostels_match
from keys.models import KeyStatus, QRCode


def _register_payload(matric, hostel, email, **extra):
    return {
        'matric_number': matric,
        'email': email,
        'hostel': hostel,
        'room_number': extra.get('room_number', '14'),
        'first_name': extra.get('first_name', 'Samuel'),
        'last_name': extra.get('last_name', 'Asije'),
        'flat_number': extra.get('flat_number', 'A1'),
        'password': 'Password123!',
        'confirm_password': 'Password123!',
    }


class AuthAndKeyFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from django.core.management import call_command
        call_command('seed_mvp_data')

    def _verify_user(self, matric):
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
        self.client.post('/api/auth/verify-email/', {
            'matric_number': matric,
            'otp': otp_code,
        }, format='json')

    def test_full_registration_and_scan_flow(self):
        matric = 'BIU/23/CSC/001'
        hostel_name = 'Hope Hostel'

        r = self.client.post('/api/auth/register/', _register_payload(
            matric, hostel_name, 'samuel.asije@example.com',
        ), format='json')
        self.assertTrue(r.data['success'])

        self._verify_user(matric)

        r = self.client.post('/api/auth/login/', {
            'identifier': matric,
            'password': 'Password123!',
        }, format='json')
        self.assertTrue(r.data['success'])
        self.assertEqual(r.data['user']['hostel'], hostel_name)
        self.assertEqual(r.data['user']['first_name'], 'Samuel')
        self.assertEqual(r.data['user']['flat_number'], 'A1')
        self.assertIsNone(r.data['user']['profile_picture'])
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

    def test_register_any_matric_without_lookup(self):
        r = self.client.post('/api/auth/register/', _register_payload(
            'BIU/NEW/999', 'Hope Hostel', 'new.student@example.com',
            first_name='New', last_name='Student',
        ), format='json')
        self.assertTrue(r.data['success'])

    def test_hostel_case_insensitive_scan(self):
        matric = 'BIU/23/CSC/002'
        r = self.client.post('/api/auth/register/', _register_payload(
            matric, 'hope hostel', 'jane.doe@example.com',
            room_number='20', first_name='Jane', last_name='Doe', flat_number='B2',
        ), format='json')
        self.assertTrue(r.data['success'])

        self._verify_user(matric)
        r = self.client.post('/api/auth/login/', {
            'identifier': matric,
            'password': 'Password123!',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["token"]}')

        from accounts.models import User
        user = User.objects.get(matric_number=matric)
        collect_qr = QRCode.objects.get(hostel='Hope Hostel', action_type='COLLECT').qr_code_id
        r = self.client.post('/api/keys/scan/', {'qr_code_id': collect_qr}, format='json')
        self.assertTrue(r.data['success'])
        self.assertTrue(hostels_match(user.profile.room.hostel, 'Hope Hostel'))

    def test_wrong_hostel_qr_rejected(self):
        matric = 'BIU/23/CSC/003'
        self.client.post('/api/auth/register/', _register_payload(
            matric, 'Peace Hostel', 'david.johnson@example.com',
            room_number='5', first_name='David', last_name='Johnson', flat_number='C3',
        ), format='json')

        self._verify_user(matric)
        r = self.client.post('/api/auth/login/', {
            'identifier': matric,
            'password': 'Password123!',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["token"]}')

        hope_collect = QRCode.objects.get(hostel='Hope Hostel', action_type='COLLECT').qr_code_id
        r = self.client.post('/api/keys/scan/', {'qr_code_id': hope_collect}, format='json')
        self.assertFalse(r.data['success'])
        self.assertEqual(r.data['message'], 'This QR code does not belong to your hostel.')

    def test_lookup_endpoint_removed(self):
        r = self.client.post('/api/auth/lookup-student/', {'matric_number': 'ANY'}, format='json')
        self.assertEqual(r.status_code, 404)

    def test_hostels_endpoint_removed(self):
        r = self.client.get('/api/hostels/')
        self.assertEqual(r.status_code, 404)
