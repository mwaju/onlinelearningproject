# Generated by Django 5.2.1 on 2025-06-07 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, unique=True),
        ),
    ]
