# Generated by Django 4.2.15 on 2024-09-04 11:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0067_chatsession_message_customercareagent_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customercareagent',
            name='user',
        ),
        migrations.RemoveField(
            model_name='message',
            name='chat_session',
        ),
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
        migrations.DeleteModel(
            name='ChatSession',
        ),
        migrations.DeleteModel(
            name='CustomerCareAgent',
        ),
        migrations.DeleteModel(
            name='Message',
        ),
    ]
