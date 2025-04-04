# Generated by Django 4.2.15 on 2024-10-16 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0123_alter_problemrequest_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='agent',
            name='user',
        ),
        migrations.AddField(
            model_name='agent',
            name='password',
            field=models.CharField(default=1, max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='agent',
            name='username',
            field=models.CharField(default=1, max_length=150, unique=True),
            preserve_default=False,
        ),
    ]
