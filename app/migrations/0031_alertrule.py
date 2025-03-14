# Generated by Django 4.2.18 on 2025-03-12 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0030_latency'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('type', models.CharField(choices=[('SYSLOG', 'Syslog'), ('MONITORING', 'Monitoring'), ('CONFIGURATION', 'Configuration')], max_length=100)),
                ('syslog_strings', models.TextField(blank=True, default='OSPF,BGP', help_text='String to match for syslog events separated by commas like OSPF,BGP etc', null=True)),
            ],
        ),
    ]
