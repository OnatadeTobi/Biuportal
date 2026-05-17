from django.contrib import admin

from hostels.models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'room_number', 'created_at')
    list_filter = ('hostel',)
    search_fields = ('room_number', 'hostel')
