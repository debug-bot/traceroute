# Generated by Django 4.2.18 on 2025-03-14 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0035_alert'),
    ]

    operations = [
        migrations.AlterField(
            model_name='router',
            name='last_pings',
            field=models.CharField(default='000', help_text="Last 3 ping results, '1' for success, '0' for failure.", max_length=3, verbose_name='Last 3 Pings'),
        ),
    ]
