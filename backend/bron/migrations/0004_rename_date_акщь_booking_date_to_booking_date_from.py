# Generated by Django 5.2 on 2025-04-30 19:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bron', '0003_rename_imgageforevents_imageforevents_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='booking',
            old_name='date_акщь',
            new_name='date_to',
        ),
        migrations.AddField(
            model_name='booking',
            name='date_from',
            field=models.DateField(default=datetime.datetime.today, verbose_name='Дата конца брони'),
        ),
    ]
