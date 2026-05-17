from django.db import models


class Room(models.Model):
    hostel = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['hostel', 'room_number']
        constraints = [
            models.UniqueConstraint(
                fields=['hostel', 'room_number'],
                name='unique_hostel_room',
            ),
        ]

    def __str__(self):
        return f'{self.hostel} Room {self.room_number}'
