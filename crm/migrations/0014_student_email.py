# Generated by Django 4.2.15 on 2024-09-03 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0013_announcement_is_personal_announcement_student'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
    ]