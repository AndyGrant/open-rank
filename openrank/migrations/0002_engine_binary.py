# Generated by Django 5.1 on 2024-08-31 09:15

import openrank.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openrank', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='engine',
            name='binary',
            field=models.FileField(blank=True, null=True, upload_to=openrank.models.engine_file_name),
        ),
    ]