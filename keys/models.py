from django.conf import settings
from django.db import models


class QRCode(models.Model):
    class ActionType(models.TextChoices):
        DROP = 'DROP', 'Drop Key'
        COLLECT = 'COLLECT', 'Collect Key'

    qr_code_id = models.CharField(max_length=100, unique=True)
    action_type = models.CharField(max_length=10, choices=ActionType.choices, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['action_type']

    def __str__(self):
        return f'{self.qr_code_id} ({self.action_type})'


class KeyStatus(models.Model):
    class Status(models.TextChoices):
        AT_PORTER = 'AT_PORTER', 'At Porter'
        WITH_STUDENT = 'WITH_STUDENT', 'With Student'

    room = models.OneToOneField('hostels.Room', on_delete=models.CASCADE, related_name='key_status')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AT_PORTER,
    )
    last_action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='key_actions',
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Key statuses'

    def __str__(self):
        return f'{self.room} - {self.status}'


class KeyActivity(models.Model):
    class ActionType(models.TextChoices):
        DROP = 'DROP', 'Drop Key'
        COLLECT = 'COLLECT', 'Collect Key'

    class ResultingStatus(models.TextChoices):
        AT_PORTER = 'AT_PORTER', 'At Porter'
        WITH_STUDENT = 'WITH_STUDENT', 'With Student'

    room = models.ForeignKey('hostels.Room', on_delete=models.CASCADE, related_name='activities')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='key_activities',
    )
    qr_code = models.ForeignKey(QRCode, on_delete=models.PROTECT, related_name='activities')
    action_type = models.CharField(max_length=10, choices=ActionType.choices)
    flat_number = models.CharField(max_length=20, blank=True, default='')
    resulting_status = models.CharField(max_length=20, choices=ResultingStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Key activities'

    def __str__(self):
        return f'{self.action_type} by {self.student.full_name} at {self.timestamp}'
