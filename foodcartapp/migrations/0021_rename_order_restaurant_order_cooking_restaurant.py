# Generated by Django 3.2.15 on 2023-02-24 07:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0020_auto_20230223_1707'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='order_restaurant',
            new_name='cooking_restaurant',
        ),
    ]