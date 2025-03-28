# Generated by Django 5.1.3 on 2024-12-31 21:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_company_contact_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deals',
            name='buyer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_buyer', to='crm.company'),
        ),
        migrations.AlterField(
            model_name='deals',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals_as_supplier', to='crm.company'),
        ),
    ]
