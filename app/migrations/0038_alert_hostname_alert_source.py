# Generated by Django 5.1.5 on 2025-03-15 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0037_alter_router_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='hostname',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='alert',
            name='source',
            field=models.CharField(default=None, max_length=100, null=True),
        ),
    ]
