# Generated by Django 4.1.4 on 2022-12-20 02:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonDRF', '0002_rating_remove_order_delivery_crew_remove_order_user_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='menuitem',
            name='featured',
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
    ]
