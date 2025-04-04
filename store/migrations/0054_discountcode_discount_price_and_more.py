# Generated by Django 4.2.15 on 2024-08-29 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0053_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='discountcode',
            name='discount_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='discountcode',
            name='discount_type',
            field=models.CharField(choices=[('percentage', 'Percentage'), ('price', 'Fixed Price')], default='percentage', max_length=10),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='discount_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
