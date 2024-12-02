# Generated by Django 4.2.15 on 2024-08-27 13:02

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('level', models.CharField(choices=[('A1', 'Beginner'), ('A2', 'Elementary'), ('B1', 'Intermediate'), ('B2', 'Upper Intermediate'), ('C1', 'Advanced'), ('C2', 'Proficiency')], max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('max_students', models.IntegerField(default=20)),
            ],
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateTimeField()),
                ('duration', models.DurationField()),
                ('max_score', models.IntegerField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.course')),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField()),
                ('specialization', models.CharField(max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField()),
                ('address', models.TextField()),
                ('emergency_contact', models.CharField(max_length=100)),
                ('level', models.CharField(choices=[('A1', 'Beginner'), ('A2', 'Elementary'), ('B1', 'Intermediate'), ('B2', 'Upper Intermediate'), ('C1', 'Advanced'), ('C2', 'Proficiency')], max_length=20)),
                ('registration_date', models.DateField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date', models.DateField(auto_now_add=True)),
                ('payment_method', models.CharField(max_length=50)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('course', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.student')),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.course')),
                ('students', models.ManyToManyField(related_name='groups', to='crm.student')),
                ('teacher', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.teacher')),
            ],
        ),
        migrations.CreateModel(
            name='ExamResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.exam')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.student')),
            ],
        ),
        migrations.CreateModel(
            name='ClassSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('room', models.CharField(max_length=50)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.group')),
            ],
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('date_posted', models.DateTimeField(auto_now_add=True)),
                ('is_global', models.BooleanField(default=False)),
                ('courses', models.ManyToManyField(blank=True, to='crm.course')),
            ],
        ),
        migrations.CreateModel(
            name='AcademicProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('comments', models.TextField(blank=True)),
                ('date', models.DateField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.student')),
            ],
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('is_present', models.BooleanField(default=False)),
                ('class_schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.classschedule')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm.student')),
            ],
            options={
                'unique_together': {('student', 'class_schedule', 'date')},
            },
        ),
    ]
