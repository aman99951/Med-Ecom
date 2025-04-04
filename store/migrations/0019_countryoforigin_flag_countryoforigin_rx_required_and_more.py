# Generated by Django 4.2.15 on 2024-08-24 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0018_inventory'),
    ]

    operations = [
        migrations.AddField(
            model_name='countryoforigin',
            name='flag',
            field=models.ImageField(blank=True, null=True, upload_to='flags/'),
        ),
        migrations.AddField(
            model_name='countryoforigin',
            name='rx_required',
            field=models.BooleanField(default=True),
        ),
        migrations.DeleteModel(
            name='CountryDetail',
        ),
    ]
