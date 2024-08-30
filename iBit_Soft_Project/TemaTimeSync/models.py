from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta


class AttendanceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    first_login = models.TimeField(null=True, blank=True)
    last_logout = models.TimeField(null=True, blank=True)
    total_hours_worked = models.DurationField(null=True, blank=True)
    is_late = models.BooleanField(default=False)

    # New fields
    expected_hours = models.IntegerField(default=9, editable=False)
    overtime = models.BooleanField(default=False)
    overtime_hours = models.DurationField(default=timedelta(0), blank=True)

    class Meta:
        unique_together = ('user', 'date')


class UserOffDay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    off_day = models.CharField(max_length=9, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])

    class Meta:
        unique_together = ('user', 'off_day')

    def __str__(self):
        return f"{self.user.username} - {self.off_day}"
