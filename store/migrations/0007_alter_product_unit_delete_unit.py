# Generated by Django 4.2.15 on 2024-08-21 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_unit_alter_product_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unit',
            field=models.CharField(max_length=50),
        ),
        migrations.DeleteModel(
            name='Unit',
        ),
    ]
