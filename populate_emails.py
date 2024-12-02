import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'english_academy_crm.settings')
django.setup()

from crm.models import Student
from django.contrib.auth.models import User

def populate_emails():
    students = Student.objects.filter(email__isnull=True)
    for student in students:
        if student.user.email:
            student.email = student.user.email
            student.save()
        else:
            print(f"El estudiante {student.user.username} no tiene email. Por favor, proporciona uno manualmente.")

if __name__ == '__main__':
    populate_emails()