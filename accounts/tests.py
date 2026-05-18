from django.test import TestCase
from rest_framework.test import APIClient

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
        self.collect_qr = QRCode.objects.get(action_type='COLLECT').qr_code_id
        self.drop_qr = QRCode.objects.get(action_type='DROP').qr_code_id

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

    def _login(self, matric):
        r = self.client.post('/api/auth/login/', {
            'identifier': matric,
            'password': 'Password123!',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["token"]}')
        return r

    def test_full_registration_and_scan_flow(self):
        matric = 'BIU/23/CSC/001'
        hostel_name = 'Hope Hostel'

        r = self.client.post('/api/auth/register/', _register_payload(
            matric, hostel_name, 'samuel.asije@example.com',
        ), format='json')
        self.assertTrue(r.data['success'])

        self._verify_user(matric)
        self._login(matric)

        r = self.client.post('/api/keys/scan/', {'qr_code_id': self.collect_qr}, format='json')
        self.assertTrue(r.data['success'])
        self.assertEqual(r.data['key_status'], KeyStatus.Status.WITH_STUDENT)
        self.assertEqual(r.data['hostel'], hostel_name)
        self.assertEqual(r.data['flat_number'], 'A1')

        r = self.client.post('/api/keys/scan/', {'qr_code_id': self.collect_qr}, format='json')
        self.assertFalse(r.data['success'])

        r = self.client.post('/api/keys/scan/', {'qr_code_id': self.drop_qr}, format='json')
        self.assertTrue(r.data['success'])
        self.assertEqual(r.data['key_status'], KeyStatus.Status.AT_PORTER)

    def test_scan_uses_profile_not_request_body(self):
        matric = 'BIU/23/CSC/002'
        self.client.post('/api/auth/register/', _register_payload(
            matric, 'Peace Hostel', 'jane.doe@example.com',
            room_number='20', flat_number='B2',
        ), format='json')
        self._verify_user(matric)
        self._login(matric)

        # Wrong hostel in body is ignored; profile Peace Hostel is used.
        r = self.client.post('/api/keys/scan/', {
            'qr_code_id': self.collect_qr,
            'hostel': 'Wrong Hostel',
            'room_number': '999',
            'flat_number': 'ZZ',
        }, format='json')
        self.assertTrue(r.data['success'])
        self.assertEqual(r.data['hostel'], 'Peace Hostel')
        self.assertEqual(r.data['room_number'], '20')
        self.assertEqual(r.data['flat_number'], 'B2')

    def test_only_two_qr_codes_exist(self):
        self.assertEqual(QRCode.objects.count(), 2)
