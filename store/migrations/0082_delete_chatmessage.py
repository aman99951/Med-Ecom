# Generated by Django 4.2.15 on 2024-09-05 11:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0081_chatrequest_chatmessage'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChatMessage',
        ),
    ]
