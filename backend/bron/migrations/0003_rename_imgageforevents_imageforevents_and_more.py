# Generated by Django 5.2 on 2025-04-30 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bron', '0002_building_event_iteminevents_iteminspaces_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ImgageForEvents',
            new_name='ImageForEvents',
        ),
        migrations.RenameModel(
            old_name='ImgageForSpaces',
            new_name='ImageForSpaces',
        ),
        migrations.AlterModelOptions(
            name='iteminspaces',
            options={'verbose_name': 'Особенности помещений', 'verbose_name_plural': 'Особенности помещений'},
        ),
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.ImageField(blank=True, default=None, upload_to='uploads/users/', verbose_name='Аватар'),
        ),
    ]
