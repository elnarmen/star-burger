# Generated by Django 3.2.15 on 2023-02-18 15:34

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0006_auto_20230218_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='called_at',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2023, 2, 18, 15, 34, 32, 299426, tzinfo=utc), null=True, verbose_name='Время звонка'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время доставки'),
        ),
    ]
