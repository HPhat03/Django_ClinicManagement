# Generated by Django 4.2.6 on 2024-02-23 11:39

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ClinicApp', '0011_alter_appointment_expecteddate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='ExpectedDate',
            field=models.DateTimeField(default=datetime.datetime(2024, 2, 23, 11, 39, 15, 498883)),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='created_date',
            field=models.DateField(default=datetime.date(2024, 2, 23)),
        ),
    ]
