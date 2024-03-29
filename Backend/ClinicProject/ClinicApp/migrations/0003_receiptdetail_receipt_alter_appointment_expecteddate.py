# Generated by Django 4.2.6 on 2024-02-07 10:53

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ClinicApp', '0002_alter_appointment_expecteddate_alter_user_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='receiptdetail',
            name='receipt',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='detail', to='ClinicApp.receipt'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='appointment',
            name='ExpectedDate',
            field=models.DateTimeField(default=datetime.datetime(2024, 2, 7, 10, 53, 31, 733937)),
        ),
    ]
