# Generated by Django 5.1.3 on 2024-12-11 00:24

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_pipeline_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deals',
            old_name='amount',
            new_name='buyer_price',
        ),
        migrations.RemoveField(
            model_name='deals',
            name='client',
        ),
        migrations.RemoveField(
            model_name='deals',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='deals',
            name='status',
        ),
        migrations.RemoveField(
            model_name='deals',
            name='title',
        ),
        migrations.AddField(
            model_name='deals',
            name='buyer',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='deals',
            name='buyer_currency',
            field=models.CharField(default='CAD', max_length=10),
        ),
        migrations.AddField(
            model_name='deals',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='deals',
            name='grade',
            field=models.CharField(default='A', max_length=50),
        ),
        migrations.AddField(
            model_name='deals',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='deals',
            name='paid_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deals',
            name='received_pallets',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='deals',
            name='received_quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='deals',
            name='scale_ticket',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='deals',
            name='shipped_pallets',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='deals',
            name='shipped_quantity',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='deals',
            name='supplier',
            field=models.CharField(default=0, max_length=255),
        ),
        migrations.AddField(
            model_name='deals',
            name='supplier_currency',
            field=models.CharField(default='CAD', max_length=10),
        ),
        migrations.AddField(
            model_name='deals',
            name='supplier_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='deals',
            name='supplier_total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='deals',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='deals',
            name='total_income_loss',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='deals',
            name='transport_company',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='deals',
            name='transport_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]