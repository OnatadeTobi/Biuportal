from django.core.management.base import BaseCommand

from keys.models import QRCode

# Two global QR codes for the porter lodge (encode only qr_code_id in the printed image).
GLOBAL_QR_CODES = {
    QRCode.ActionType.COLLECT: 'qr_live_collect_B82K10QZ91MN',
    QRCode.ActionType.DROP: 'qr_live_drop_9F3K92XQ1PZ7',
}


class Command(BaseCommand):
    help = 'Seed the two global QR codes (DROP + COLLECT).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding global QR codes...\n'))

        for action_type, qr_code_id in GLOBAL_QR_CODES.items():
            qr, created = QRCode.objects.update_or_create(
                action_type=action_type,
                defaults={
                    'qr_code_id': qr_code_id,
                    'is_active': True,
                },
            )
            label = 'Created' if created else 'Updated'
            self.stdout.write(f'  {action_type}: {qr.qr_code_id} ({label})')

        self.stdout.write(
            self.style.SUCCESS(
                '\nDone. Print two QR images:\n'
                f'  COLLECT: {GLOBAL_QR_CODES[QRCode.ActionType.COLLECT]}\n'
                f'  DROP:    {GLOBAL_QR_CODES[QRCode.ActionType.DROP]}'
            )
        )
