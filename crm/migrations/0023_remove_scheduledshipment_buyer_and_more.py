# Generated by Django 5.1.5 on 2025-07-03 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0022_scaleticketstatus'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduledshipment',
            name='buyer',
        ),
        migrations.RemoveField(
            model_name='scheduledshipment',
            name='date',
        ),
        migrations.RemoveField(
            model_name='scheduledshipment',
            name='grade',
        ),
        migrations.RemoveField(
            model_name='scheduledshipment',
            name='is_done',
        ),
        migrations.RemoveField(
            model_name='scheduledshipment',
            name='supplier',
        ),
        migrations.RemoveField(
            model_name='scheduledshipment',
            name='time',
        ),
        migrations.AddField(
            model_name='scheduledshipment',
            name='is_recurring',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scheduledshipment',
            name='recurrence_day',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scheduledshipment',
            name='recurrence_type',
            field=models.CharField(blank=True, choices=[('weekly', 'Weekly'), ('biweekly', 'Every 2 Weeks'), ('monthly', 'Monthly')], max_length=20, null=True),
        ),
    ]
