# Generated by Django 4.2.15 on 2024-08-28 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0039_discountcode'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='discount_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.discountcode'),
        ),
    ]
