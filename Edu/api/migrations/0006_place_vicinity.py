# Generated by Django 5.2 on 2025-04-23 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_remove_place_latitude_remove_place_longitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='vicinity',
            field=models.TextField(blank=True, null=True),
        ),
    ]
