# Generated by Django 5.0 on 2024-02-22 18:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chat', '0001_initial'),
        ('eLearning', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chatroom',
            name='course',
            field=models.OneToOneField(help_text='The course associated with this chat room.', on_delete=django.db.models.deletion.CASCADE, related_name='chat_room', to='eLearning.course'),
        ),
        migrations.AddField(
            model_name='chatmembership',
            name='chat_room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.chatroom'),
        ),
        migrations.AddField(
            model_name='message',
            name='chat_room',
            field=models.ForeignKey(help_text='The chat room this message belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.chatroom'),
        ),
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(help_text='The user who sent the message.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chatmembership',
            name='last_viewed_message',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.message'),
        ),
        migrations.AlterUniqueTogether(
            name='chatroom',
            unique_together={('course', 'chat_name')},
        ),
    ]
