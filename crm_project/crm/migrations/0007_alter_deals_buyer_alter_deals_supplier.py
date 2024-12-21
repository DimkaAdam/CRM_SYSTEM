# Generated by Django 5.1.3 on 2024-12-18 00:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0006_rename_type_client_client_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deals',
            name='buyer',
            field=models.ForeignKey(blank=True, limit_choices_to={'client_type': 'buyer'}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_buyer', to='crm.client'),
        ),
        migrations.AlterField(
            model_name='deals',
            name='supplier',
            field=models.ForeignKey(limit_choices_to={'client_type': 'supplier'}, on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_supplier', to='crm.client'),
        ),
    ]