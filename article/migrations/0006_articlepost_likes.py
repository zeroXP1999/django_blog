# Generated by Django 2.2 on 2019-12-08 05:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0005_articlepost_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='articlepost',
            name='likes',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
