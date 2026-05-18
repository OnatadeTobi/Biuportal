import accounts.models
from django.db import migrations, models


def populate_profile_names(apps, schema_editor):
    StudentProfile = apps.get_model('accounts', 'StudentProfile')
    for profile in StudentProfile.objects.select_related('user').iterator():
        parts = profile.user.full_name.split(None, 1)
        profile.first_name = parts[0] if parts else 'Student'
        profile.last_name = parts[1] if len(parts) > 1 else ''
        if not profile.flat_number:
            profile.flat_number = 'N/A'
        profile.save(update_fields=['first_name', 'last_name', 'flat_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='first_name',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='last_name',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='flat_number',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.RunPython(populate_profile_names, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='studentprofile',
            name='first_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='last_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='flat_number',
            field=models.CharField(max_length=20),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='profile_picture',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=accounts.models.profile_picture_upload_path,
            ),
        ),
    ]
