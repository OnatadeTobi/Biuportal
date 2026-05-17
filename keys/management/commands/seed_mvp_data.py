import secrets
import string

from django.core.management.base import BaseCommand

from hostels.utils import MVP_HOSTEL_NAMES, canonicalize_hostel
from keys.models import QRCode

HOSTEL_SLUGS = {
    'Hope Hostel': 'hope',
    'Above Only Hostel': 'above_only',
    'Peace Hostel': 'peace',
    'Balm of Gilead': 'balm_of_gilead',
    'Grace Hostel': 'grace',
}

PREDEFINED_QR_IDS = {
    'Hope Hostel': {
        'DROP': 'qr_live_hope_drop_9F3K92XQ1PZ7',
        'COLLECT': 'qr_live_hope_collect_B82K10QZ91MN',
    },
    'Above Only Hostel': {
        'DROP': 'qr_live_above_only_drop_83KSJS9272HD',
        'COLLECT': 'qr_live_above_only_collect_92JSKSHD772X',
    },
    'Peace Hostel': {
        'DROP': 'qr_live_peace_drop_K7J2M9X4P1Q8',
        'COLLECT': 'qr_live_peace_collect_R3N8V5W2T6Y1',
    },
    'Balm of Gilead': {
        'DROP': 'qr_live_balm_of_gilead_drop_A4B7C9D2E5F8',
        'COLLECT': 'qr_live_balm_of_gilead_collect_G1H3J6K8L0M2',
    },
    'Grace Hostel': {
        'DROP': 'qr_live_grace_drop_N5P8Q1R4S7T0',
        'COLLECT': 'qr_live_grace_collect_U2V5W8X1Y4Z7',
    },
}


def _random_suffix(length=12):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _qr_id(hostel_name, action_type):
    predefined = PREDEFINED_QR_IDS.get(hostel_name, {}).get(action_type)
    if predefined:
        return predefined
    slug = HOSTEL_SLUGS[hostel_name]
    action = action_type.lower()
    return f'qr_live_{slug}_{action}_{_random_suffix()}'


class Command(BaseCommand):
    help = 'Seed MVP QR codes (DROP + COLLECT per known hostel name).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding QR codes...\n'))

        for hostel_name in MVP_HOSTEL_NAMES:
            canonical = canonicalize_hostel(hostel_name)
            self.stdout.write(self.style.SUCCESS(f'\n{canonical}'))

            for action_type in (QRCode.ActionType.DROP, QRCode.ActionType.COLLECT):
                qr_code_id = _qr_id(canonical, action_type)
                qr, qr_created = QRCode.objects.update_or_create(
                    hostel=canonical,
                    action_type=action_type,
                    defaults={
                        'qr_code_id': qr_code_id,
                        'is_active': True,
                    },
                )
                label = 'Created' if qr_created else 'Updated'
                self.stdout.write(f'  {action_type}: {qr.qr_code_id} ({label})')

        self.stdout.write(
            self.style.SUCCESS('\nMVP seed complete. Use the QR code IDs above for testing scans.')
        )
