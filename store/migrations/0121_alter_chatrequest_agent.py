# Generated by Django 4.2.15 on 2024-10-16 03:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0120_alter_chatmessage_sender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chatrequest',
            name='agent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_requests', to='store.agent'),
        ),
    ]
