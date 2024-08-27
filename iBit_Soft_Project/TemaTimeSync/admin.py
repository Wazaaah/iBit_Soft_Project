from django.contrib import admin
from .models import AttendanceRecord


# Register your models here.
@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'first_login', 'last_logout', 'total_hours_worked')
