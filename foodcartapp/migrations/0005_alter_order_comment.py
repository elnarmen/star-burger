# Generated by Django 3.2.15 on 2023-02-18 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0004_auto_20230218_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, max_length=255, verbose_name='Комментарий'),
        ),
    ]