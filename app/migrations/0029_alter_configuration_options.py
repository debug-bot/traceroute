# Generated by Django 5.1.5 on 2025-03-10 11:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0028_configuration'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='configuration',
            options={'ordering': ['-created_at']},
        ),
    ]
