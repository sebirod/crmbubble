from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
from .models import (
    Student, FamilyMember, Teacher, Course, Group, ClassSchedule,
    Attendance, AcademicProgress, Exam, ExamResult, Payment, Announcement, Enrollment, CompanyInfo
)

class StudentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'email', 'date_of_birth', 'address',
            'emergency_contact', 'level', 'document_type', 'document_number',
            'nationality', 'profile_photo'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.user.pk if self.instance.pk else None).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

    def save(self, commit=True):
        user = self.instance.user if self.instance.pk else None
        if user is None:
            user = User.objects.create_user(
                username=self.cleaned_data['email'],
                email=self.cleaned_data['email'],
                password=User.objects.make_random_password(),
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
        else:
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.username = self.cleaned_data['email']
            user.save()

        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
        return student

class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ['relationship', 'first_name', 'last_name', 'phone', 'email']

FamilyMemberFormSet = forms.inlineformset_factory(Student, FamilyMember, form=FamilyMemberForm, extra=1, can_delete=True)

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ('bio', 'specialization')

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('name', 'description', 'level', 'start_date', 'end_date', 'max_students')

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'course', 'teacher')

class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = ('group', 'day_of_week', 'start_time', 'end_time', 'room')

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ('student', 'class_schedule', 'date', 'is_present')

class AcademicProgressForm(forms.ModelForm):
    class Meta:
        model = AcademicProgress
        fields = [
            'student', 'course', 'comprehension_oral', 'expression_oral', 
            'comprehension_written', 'expression_written', 'grammar', 
            'vocabulary', 'participation', 'homework', 'behavior', 
            'evaluations', 'comments', 'date'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fields = ['comprehension_oral', 'expression_oral', 'comprehension_written', 
                  'expression_written', 'grammar', 'vocabulary', 'participation', 
                  'homework', 'behavior', 'evaluations']
        for field in fields:
            value = cleaned_data.get(field)
            if value is not None and (value < 0 or value > 10):
                self.add_error(field, f"{field.replace('_', ' ').title()} must be between 0.0 and 10.0")

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ('course', 'name', 'date', 'duration', 'max_score')

class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ('student', 'exam', 'score')

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['enrollment', 'amount', 'payment_method', 'bank_account', 'bank_name', 'is_confirmed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].required = False
        if self.instance and self.instance.enrollment:
            self.fields['amount'].initial = self.instance.enrollment.total_cost

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('payment_method') == 'transfer' and (not cleaned_data.get('bank_account') or not cleaned_data.get('bank_name')):
            raise forms.ValidationError("Los campos de cuenta bancaria son requeridos para transferencias.")
        return cleaned_data

class EnrollmentForm(forms.ModelForm):
    total_cost = forms.DecimalField(required=False, decimal_places=2, max_digits=10)
    total_cost_with_vat = forms.DecimalField(required=False, decimal_places=2, max_digits=10)

    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'group', 'annual_cost', 'monthly_cost', 'hourly_cost', 'vat_rate', 'total_cost', 'total_cost_with_vat']

    def clean(self):
        cleaned_data = super().clean()
        annual_cost = cleaned_data.get('annual_cost', 0)
        monthly_cost = cleaned_data.get('monthly_cost', 0)
        hourly_cost = cleaned_data.get('hourly_cost', 0)
        
        # Recalculate total cost and VAT
        total_cost = annual_cost + monthly_cost + hourly_cost
        vat_rate = cleaned_data.get('vat_rate', 21.00)  # IVA en porcentaje
        vat_amount = (total_cost * vat_rate) / 100
        total_cost_with_vat = total_cost + vat_amount
        
        # Set the recalculated values
        cleaned_data['total_cost'] = total_cost
        cleaned_data['total_cost_with_vat'] = total_cost_with_vat
        
        return cleaned_data

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'content', 'courses', 'is_global')

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class CompanyInfoForm(forms.ModelForm):
    class Meta:
        model = CompanyInfo
        fields = ['name', 'fiscal_number', 'fiscal_address', 'phone', 'email', 'website', 'logo']
        widgets = {
            'fiscal_address': forms.Textarea(attrs={'rows': 3}),
            'logo': forms.FileInput(),
        }

    def clean_fiscal_number(self):
        fiscal_number = self.cleaned_data.get('fiscal_number')
        # Aquí puedes añadir validación específica para el formato CIF/NIF si lo deseas
        return fiscal_number

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            if logo.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("El tamaño de la imagen no debe exceder 5MB.")
            import os
            ext = os.path.splitext(logo.name)[1]
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not ext.lower() in valid_extensions:
                raise forms.ValidationError("Formato de archivo no soportado. Use jpg, jpeg, png o gif.")
        return logo

class UserChangePasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
