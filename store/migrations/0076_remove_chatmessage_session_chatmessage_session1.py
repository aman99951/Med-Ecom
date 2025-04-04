# Generated by Django 4.2.15 on 2024-09-05 10:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0075_remove_chatmessage_sender1_chatmessage_sender2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chatmessage',
            name='session',
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='session1',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='store.chatrequest'),
        ),
    ]
