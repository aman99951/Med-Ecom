# Generated by Django 4.2.15 on 2024-08-28 14:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0035_delete_billinginfo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address',
            old_name='address_line1',
            new_name='address_1',
        ),
        migrations.RenameField(
            model_name='address',
            old_name='address_line2',
            new_name='address_2',
        ),
    ]
