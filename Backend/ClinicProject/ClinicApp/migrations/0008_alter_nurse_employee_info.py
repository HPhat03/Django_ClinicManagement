# Generated by Django 4.2.6 on 2024-01-29 03:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ClinicApp', '0007_alter_confirmation_appointment_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nurse',
            name='employee_info',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='nurse_info', serialize=False, to='ClinicApp.employee'),
        ),
    ]
