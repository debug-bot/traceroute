# Generated by Django 4.2.18 on 2025-03-03 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_alter_category_options_category_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='router',
            name='consecutive_failures',
            field=models.PositiveIntegerField(default=0, help_text='Number of consecutive failures', verbose_name='Consecutive Failures'),
        ),
        migrations.AddField(
            model_name='router',
            name='cpu_usage',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='router',
            name='mem_usage',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='router',
            name='status',
            field=models.CharField(choices=[('online', 'Online'), ('offline', 'Offline'), ('warning', 'Warning')], default='offline', help_text='Current status of the device', max_length=10, verbose_name='Device Status'),
        ),
        migrations.AddField(
            model_name='router',
            name='storage_usage',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='router',
            name='successful_pings',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='router',
            name='total_pings',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
