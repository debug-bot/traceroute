# Generated by Django 4.2.18 on 2025-03-03 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_router_last_pings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='router',
            name='last_pings',
            field=models.CharField(default='', help_text="Last 3 ping results, '1' for success, '0' for failure.", max_length=3, verbose_name='Last Pings'),
        ),
    ]
