# Generated by Django 5.1.4 on 2025-01-07 00:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0004_contact_current_price_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AlterField(
            model_name='deals',
            name='received_quantity',
            field=models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='deals',
            name='shipped_quantity',
            field=models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=10, null=True),
        ),
        migrations.CreateModel(
            name='ContactMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('material', models.CharField(choices=[('Baled Cardboard', 'Baled Cardboard'), ('Flexible Plastic', 'Flexible Plastic'), ('Mixed Container', 'Mixed Container'), ('Pallets', 'Pallets'), ('Kraft Paper Bags', 'Kraft Paper Bags'), ('Loose Cardboard', 'Loose Cardboard'), ('Cardboard in Loose', 'Cardboard in Loose')], max_length=255)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contact_materials', to='crm.contact')),
            ],
        ),
    ]
