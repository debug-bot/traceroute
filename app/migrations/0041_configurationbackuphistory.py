# Generated by Django 4.2.18 on 2025-03-20 21:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0040_router_only_monitor'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigurationBackupHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('success', models.BooleanField(default=False)),
                ('configuration', models.ForeignKey(help_text='Configuration backup history', on_delete=django.db.models.deletion.CASCADE, to='app.configuration')),
            ],
        ),
    ]
