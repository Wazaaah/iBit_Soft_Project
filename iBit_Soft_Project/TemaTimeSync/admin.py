from django.contrib import admin
from .models import AttendanceRecord, UserOffDay


# Register your models here.
@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'first_login', 'is_late', 'last_logout', 'expected_hours', 'total_hours_worked',
                    'overtime', 'overtime_hours')


@admin.register(UserOffDay)
class UserOffDayAdmin(admin.ModelAdmin):
    list_display = ('user', 'off_day')
