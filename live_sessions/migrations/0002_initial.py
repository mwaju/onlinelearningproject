# Generated by Django 5.2.1 on 2025-05-23 14:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('live_sessions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='livesession',
            name='instructor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conducted_sessions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sessionchat',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chats', to='live_sessions.livesession'),
        ),
        migrations.AddField(
            model_name='sessionchat',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_chats', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sessionparticipant',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='live_sessions.livesession'),
        ),
        migrations.AddField(
            model_name='sessionparticipant',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attended_sessions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='sessionparticipant',
            unique_together={('session', 'user')},
        ),
    ]
