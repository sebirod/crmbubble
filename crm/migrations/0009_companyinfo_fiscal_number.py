# Generated by Django 4.2.15 on 2024-08-30 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0008_remove_payment_bank_routing_remove_payment_card_cvc_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='companyinfo',
            name='fiscal_number',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True, verbose_name='CIF/NIF'),
        ),
    ]
