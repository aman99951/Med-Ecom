# Generated by Django 4.2.15 on 2024-10-17 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0125_alter_agent_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatrequest',
            name='guest_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
