# Generated by Django 4.2.15 on 2024-09-09 15:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0102_remove_healthinformation_order_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthinformation',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
