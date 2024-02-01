# Generated by Django 4.2.6 on 2024-01-31 07:04

import ckeditor.fields
import cloudinary.models
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ClinicApp', '0009_receipt_service_medicinedetails_total_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='diploma',
            field=ckeditor.fields.RichTextField(),
        ),
        migrations.AlterField(
            model_name='medicine',
            name='content',
            field=ckeditor.fields.RichTextField(),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2024, 1, 31, 14, 4, 9, 291375)),
        ),
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=cloudinary.models.CloudinaryField(default='https://res.cloudinary.com/dzm6ikgbo/image/upload/v1704261125/plxne6rgmefyzkx4mdzz.png', max_length=255, verbose_name='image'),
        ),
    ]
