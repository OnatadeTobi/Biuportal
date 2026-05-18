from django.db import migrations, models


def seed_global_qr_codes(apps, schema_editor):
    QRCode = apps.get_model('keys', 'QRCode')
    QRCode.objects.all().delete()
    QRCode.objects.create(
        qr_code_id='qr_live_collect_B82K10QZ91MN',
        action_type='COLLECT',
        is_active=True,
    )
    QRCode.objects.create(
        qr_code_id='qr_live_drop_9F3K92XQ1PZ7',
        action_type='DROP',
        is_active=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('keys', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='keyactivity',
            name='flat_number',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.RemoveConstraint(
            model_name='qrcode',
            name='unique_active_qr_per_hostel_action',
        ),
        migrations.RemoveField(
            model_name='qrcode',
            name='hostel',
        ),
        migrations.RunPython(seed_global_qr_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='qrcode',
            name='action_type',
            field=models.CharField(
                choices=[('DROP', 'Drop Key'), ('COLLECT', 'Collect Key')],
                max_length=10,
                unique=True,
            ),
        ),
        migrations.AlterModelOptions(
            name='qrcode',
            options={'ordering': ['action_type']},
        ),
    ]
