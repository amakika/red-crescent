# Generated by Django 5.1.5 on 2025-01-25 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volonteer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='total_hours',
            field=models.FloatField(default=0.0),
        ),
    ]
