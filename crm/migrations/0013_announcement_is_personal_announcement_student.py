# Generated by Django 4.2.15 on 2024-09-01 15:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0012_alter_payment_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='is_personal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='announcement',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='crm.student'),
        ),
    ]
