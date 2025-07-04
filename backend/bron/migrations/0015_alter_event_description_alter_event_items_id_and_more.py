# Generated by Django 5.2 on 2025-05-13 20:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bron', '0014_alter_event_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.CharField(blank=True, max_length=255, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='event',
            name='items_id',
            field=models.ManyToManyField(blank=True, to='bron.iteminevents', verbose_name='Особенности'),
        ),
        migrations.AlterField(
            model_name='event',
            name='space_id',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, to='bron.space', verbose_name='Помещение'),
        ),
        migrations.AlterField(
            model_name='organizer',
            name='description',
            field=models.CharField(blank=True, max_length=255, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='spacesreview',
            name='add_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления'),
        ),
    ]
