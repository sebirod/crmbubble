# Generated by Django 4.2.15 on 2024-08-30 11:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0004_remove_payment_course_remove_payment_student_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.enrollment'),
        ),
    ]
