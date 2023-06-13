# Generated by Django 3.2.18 on 2023-04-26 19:20

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0012_auto_20230228_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='componentsubscription',
            name='missing_components',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=1024), blank=True, default=list, null=True, size=None),
        ),
    ]