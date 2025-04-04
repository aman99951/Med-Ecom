# Generated by Django 4.2.15 on 2024-08-29 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0052_rename_shipping_order_shipping_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('canceled', 'Canceled'), ('returned', 'Returned')], default='pending', max_length=50),
        ),
    ]
