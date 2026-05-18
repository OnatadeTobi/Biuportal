from django.contrib import admin

from keys.models import KeyActivity, KeyStatus, QRCode


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('qr_code_id', 'action_type', 'is_active', 'created_at')
    list_filter = ('action_type', 'is_active')
    search_fields = ('qr_code_id',)


@admin.register(KeyStatus)
class KeyStatusAdmin(admin.ModelAdmin):
    list_display = ('room', 'status', 'last_action_by', 'last_updated')
    list_filter = ('status',)
    search_fields = ('room__room_number', 'room__hostel')


@admin.register(KeyActivity)
class KeyActivityAdmin(admin.ModelAdmin):
    list_display = ('room', 'student', 'action_type', 'flat_number', 'resulting_status', 'timestamp')
    list_filter = ('action_type', 'resulting_status')
    search_fields = ('student__full_name', 'room__room_number', 'room__hostel', 'flat_number')
    raw_id_fields = ('room', 'student', 'qr_code')
