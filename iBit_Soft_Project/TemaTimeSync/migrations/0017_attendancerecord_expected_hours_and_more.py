# Generated by Django 4.2.3 on 2024-08-29 16:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TemaTimeSync', '0016_useroffday'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='expected_hours',
            field=models.IntegerField(default=9, editable=False),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='overtime',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='overtime_hours',
            field=models.DurationField(blank=True, default=datetime.timedelta(0)),
        ),
    ]