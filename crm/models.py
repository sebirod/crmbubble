from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True, null=True, blank=True)
    date_of_birth = models.DateField()
    address = models.TextField()
    emergency_contact = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=[
        ('A1', 'Beginner'),
        ('A2', 'Elementary'),
        ('B1', 'Intermediate'),
        ('B2', 'Upper Intermediate'),
        ('C1', 'Advanced'),
        ('C2', 'Proficiency'),
    ])
    registration_date = models.DateField(auto_now_add=True)
    document_type = models.CharField(max_length=20, choices=[
        ('DNI', 'DNI'),
        ('NIE', 'NIE'),
        ('CIF', 'CIF'),
        ('PASSPORT', 'Passport'),
    ], null=True, blank=True)
    document_number = models.CharField(max_length=20, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def save(self, *args, **kwargs):
        if not self.email:
            self.email = self.user.email
        super().save(*args, **kwargs)

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def overall_score(self):
        academic_records = AcademicProgress.objects.filter(student=self)
        if not academic_records.exists():
            return None

        total_score = 0
        total_records = academic_records.count()

        for record in academic_records:
            total_score += (
                record.comprehension_oral + record.expression_oral +
                record.comprehension_written + record.expression_written +
                record.grammar + record.vocabulary +
                record.participation + record.homework +
                record.behavior + record.evaluations
            ) / 10

        return round(total_score / total_records, 2)

    @property
    def attendance_score(self):
        total_classes = Attendance.objects.filter(student=self).count()
        if total_classes == 0:
            return None
        attended_classes = Attendance.objects.filter(student=self, is_present=True).count()
        return round((attended_classes / total_classes) * 100, 2)

    @property
    def is_student(self):
        return hasattr(self, 'student')

@receiver(post_save, sender=User)
def create_or_update_student_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        Student.objects.create(user=instance, email=instance.email)
    elif not instance.is_staff:
        instance.student.save()

class FamilyMember(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='family_members')
    relationship = models.CharField(max_length=20, choices=[
        ('FATHER', 'Father'),
        ('MOTHER', 'Mother'),
        ('UNCLE', 'Uncle'),
        ('AUNT', 'Aunt'),
        ('GRANDFATHER', 'Grandfather'),
        ('GRANDMOTHER', 'Grandmother'),
        ('OTHER', 'Other'),
    ])
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_relationship_display()} of {self.student}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=[
        ('A1', 'Beginner'),
        ('A2', 'Elementary'),
        ('B1', 'Intermediate'),
        ('B2', 'Upper Intermediate'),
        ('C1', 'Advanced'),
        ('C2', 'Proficiency'),
    ])
    start_date = models.DateField()
    end_date = models.DateField()
    max_students = models.IntegerField(default=20)

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    students = models.ManyToManyField(Student, related_name='groups')

    def __str__(self):
        return f"{self.name} - {self.course.name}"

class ClassSchedule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=[(i, i) for i in range(7)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.group.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'class_schedule', 'date')

    def __str__(self):
        return f"{self.student} - {self.class_schedule} - {self.date}"

class AcademicProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    comprehension_oral = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    expression_oral = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    comprehension_written = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    expression_written = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    grammar = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    vocabulary = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    participation = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    homework = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    behavior = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    evaluations = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(10.0)], default=0.0)
    comments = models.TextField(blank=True)
    date = models.DateField()

    @property
    def overall_score(self):
        total_score = (
            self.comprehension_oral +
            self.expression_oral +
            self.comprehension_written +
            self.expression_written +
            self.grammar +
            self.vocabulary +
            self.participation +
            self.homework +
            self.behavior +
            self.evaluations
        )
        num_fields = 10
        return total_score / num_fields

    def get_description(self, score):
        if 0 <= score <= 3.99:
            return "Escaso"
        elif 4.0 <= score <= 5.99:
            return "Suficiente"
        elif 6.0 <= score <= 7.99:
            return "Bien"
        elif 8.0 <= score <= 9.99:
            return "Muy Bien"
        elif 10.0 <= score:
            return "Excelente"
        return "No calificado"

    def __str__(self):
        return f"{self.student} - {self.course} - {self.date}"

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date = models.DateTimeField()
    duration = models.DurationField()
    max_score = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.course.name}"

class ExamResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"{self.student} - {self.exam.name} - {self.score}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField(auto_now_add=True)
    annual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    hourly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=21.00)
    total_cost_with_vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.total_cost = self.annual_cost + self.monthly_cost + self.hourly_cost
        vat_amount = (self.total_cost * self.vat_rate) / 100
        self.total_cost_with_vat = self.total_cost + vat_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.course.name}"

class Payment(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_date = models.DateField(default=timezone.now)
    bank_account = models.CharField(max_length=34, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    is_confirmed = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer'),
    ], default='cash')

    def save(self, *args, **kwargs):
        if self.amount == 0 and self.enrollment:
            self.amount = self.enrollment.total_cost_with_vat
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enrollment} - {self.amount} - {self.payment_date}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    courses = models.ManyToManyField(Course, blank=True)
    is_global = models.BooleanField(default=False)
    is_personal = models.BooleanField(default=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title

class CompanyInfo(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre de la empresa")
    fiscal_number = models.CharField(max_length=20, verbose_name="CIF/NIF", unique=True)
    fiscal_address = models.TextField(verbose_name="Dirección fiscal")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Correo electrónico")
    website = models.URLField(verbose_name="Sitio web", blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name="Logo de la empresa")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Información de la empresa"
        verbose_name_plural = "Información de la empresa"