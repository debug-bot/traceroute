# Generated by Django 5.1.5 on 2025-02-02 06:31

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_popularcommand'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='popularcommand',
            name='label',
        ),
        migrations.RemoveField(
            model_name='popularcommand',
            name='purpose',
        ),
        migrations.AddField(
            model_name='popularcommand',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, help_text='Timestamp when the command was executed'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='popularcommand',
            name='command',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.command'),
        ),
    ]
