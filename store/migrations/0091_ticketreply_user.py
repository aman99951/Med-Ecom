# Generated by Django 4.2.15 on 2024-09-07 15:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0090_ticket_attachments_ticket_deparment'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketreply',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
