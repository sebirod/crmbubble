# Generated by Django 4.2.15 on 2024-08-29 17:02

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_student_document_number_student_document_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='academicprogress',
            name='grade',
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='behavior',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='comprehension_oral',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='comprehension_written',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='evaluations',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='expression_oral',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='expression_written',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='grammar',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='homework',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='participation',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
        migrations.AddField(
            model_name='academicprogress',
            name='vocabulary',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
    ]
