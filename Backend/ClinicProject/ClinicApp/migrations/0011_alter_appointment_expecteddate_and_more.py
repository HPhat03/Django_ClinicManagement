# Generated by Django 4.2.6 on 2024-02-22 19:19

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ClinicApp', '0010_healthrecord_overview_alter_appointment_expecteddate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='ExpectedDate',
            field=models.DateTimeField(default=datetime.datetime(2024, 2, 22, 19, 19, 21, 944203)),
        ),
        migrations.AlterField(
            model_name='doctor',
            name='employee_info',
            field=models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='doctor_info', serialize=False, to='ClinicApp.employee'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='user_info',
            field=models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='employee', serialize=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='nurse',
            name='employee_info',
            field=models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='nurse_info', serialize=False, to='ClinicApp.employee'),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='created_date',
            field=models.DateField(default=datetime.date(2024, 2, 22)),
        ),
    ]
