from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import EmailVerificationOTP, StudentProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('full_name', 'email', 'matric_number', 'is_email_verified', 'is_active', 'is_staff')
    list_filter = ('is_email_verified', 'is_active', 'is_staff')
    search_fields = ('full_name', 'email', 'matric_number')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'matric_number')}),
        ('Verification', {'fields': ('is_email_verified',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'matric_number', 'full_name', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'created_at')
    search_fields = ('user__full_name', 'user__matric_number', 'room__room_number')
    raw_id_fields = ('user', 'room')


@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('user__matric_number', 'user__email')
    raw_id_fields = ('user',)
