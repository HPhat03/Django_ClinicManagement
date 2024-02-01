# Generated by Django 4.2.6 on 2024-01-31 07:20

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ClinicApp', '0011_alter_medicine_image_alter_receipt_created_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctor',
            name='departments',
        ),
        migrations.AlterField(
            model_name='receipt',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 1, 31, 14, 20, 34, 825461)),
        ),
        migrations.AddField(
            model_name='doctor',
            name='departments',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='doctors', to='ClinicApp.department'),
        ),
    ]
