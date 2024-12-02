import os, logging
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import update_session_auth_hash, get_user_model
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, cm 
from reportlab.platypus import Paragraph, Spacer, Image
from reportlab.lib.enums import TA_RIGHT
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet  # Mantenido
from io import BytesIO
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Avg, F, Q, Sum, FloatField, ExpressionWrapper, fields
from django.db.models.functions import Cast
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
import tempfile
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import (
    Student, Teacher, Course, Group, ClassSchedule, Attendance,
    AcademicProgress, Exam, ExamResult, Payment, Announcement, Enrollment, CompanyInfo
)
from .forms import (
    StudentForm, FamilyMemberFormSet, TeacherForm, CourseForm, GroupForm,
    ClassScheduleForm, AttendanceForm, AcademicProgressForm, ExamForm,
    ExamResultForm, PaymentForm, AnnouncementForm, EnrollmentForm
)

logger = logging.getLogger(__name__)
User = get_user_model()

class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'crm/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = Student.objects.get(user=self.request.user)
        enrollments = Enrollment.objects.filter(student=student)

        # Próximo examen
        next_exam = Exam.objects.filter(
            course__in=enrollments.values('course'),
            date__gte=timezone.now()
        ).order_by('date').first()

        # Anuncios recientes
        all_announcements = Announcement.objects.filter(
            Q(is_global=True) |
            Q(courses__in=enrollments.values('course')) |
            Q(is_personal=True, student=student)
        ).distinct().order_by('-date_posted')

        paginator = Paginator(all_announcements, 5)  # 5 anuncios por página

        # Obtener número de página de la URL, por defecto 1
        page_number = self.request.GET.get('page', 1)
        
        try:
            page_number = int(page_number)
            page_obj = paginator.page(page_number)
        except (ValueError, EmptyPage):
            # Si el número de página es inválido, mostrar la primera página
            page_obj = paginator.page(1)

        
        # Progreso reciente y cálculo del progreso general
        recent_progress = AcademicProgress.objects.filter(student=student).order_by('-date')[:5]

        progress_fields = ['comprehension_oral', 'expression_oral', 'comprehension_written', 
                           'expression_written', 'grammar', 'vocabulary', 'participation', 
                           'homework', 'behavior', 'evaluations']
        
        overall_progress = 0
        progress_count = 0
        progress_data = []

        for progress in recent_progress:
            field_sum = sum(getattr(progress, field) for field in progress_fields)
            avg_score = field_sum / len(progress_fields)
            overall_progress += avg_score
            progress_count += 1
            
            progress_data.append({
                'date': progress.date.strftime('%b %d'),
                'score': round(avg_score, 2)
            })

        overall_progress = round(overall_progress / progress_count if progress_count > 0 else 0, 2)

        # Resultados de exámenes recientes
        recent_exam_results = ExamResult.objects.filter(student=student).order_by('-exam__date')[:5]

        # Asistencias recientes
        recent_attendances = Attendance.objects.filter(student=student).order_by('-date')[:5]

        context.update({
            'student': student,
            'enrollments': enrollments,
            'next_exam': next_exam,
            'recent_announcements': page_obj.object_list,
            'page_obj': page_obj,
            'recent_progress': progress_data,
            'overall_progress': overall_progress,
            'recent_exam_results': recent_exam_results,
            'recent_attendances': recent_attendances,
            'company_info': CompanyInfo.objects.first(),
        })
        return context   
    

class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'crm/student_form.html'
    success_url = reverse_lazy('student_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['family_members'] = FamilyMemberFormSet(self.request.POST)
        else:
            data['family_members'] = FamilyMemberFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        family_members = context['family_members']
        with transaction.atomic():
            self.object = form.save()
            if family_members.is_valid():
                family_members.instance = self.object
                family_members.save()
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff

class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'crm/student_form.html'
    success_url = reverse_lazy('student_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['family_members'] = FamilyMemberFormSet(self.request.POST, instance=self.object)
        else:
            data['family_members'] = FamilyMemberFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        family_members = context['family_members']
        with transaction.atomic():
            self.object = form.save()
            if family_members.is_valid():
                family_members.instance = self.object
                family_members.save()
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff

class StudentListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = Student
    template_name = 'crm/student_list.html'
    context_object_name = 'students'
    paginate_by = 10

    def get_queryset(self):
        today = timezone.now().date()
        return Student.objects.annotate(
            age=ExpressionWrapper(
                (today - F('date_of_birth')) / 365.25,
                output_field=fields.IntegerField()
            )
        ).select_related('user').prefetch_related('groups')

    def test_func(self):
        return self.request.user.is_staff

class StudentDetailView(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    model = Student
    template_name = 'crm/student_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object
        
        # Obtener la inscripción más reciente del estudiante
        enrollment = Enrollment.objects.filter(student=student).order_by('-start_date').first()
        
        if enrollment:
            context['enrollment'] = enrollment
            context['course'] = enrollment.course
            context['group'] = enrollment.group
        
        return context

    def test_func(self):
        return self.request.user.is_staff or self.request.user == self.get_object().user
    

class CourseListView(LoginRequiredMixin, generic.ListView):
    model = Course
    template_name = 'crm/course_list.html'
    context_object_name = 'courses'
    paginate_by = 10

class CourseDetailView(LoginRequiredMixin, generic.DetailView):
    model = Course
    template_name = 'crm/course_detail.html'

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'crm/course_form.html'
    success_url = reverse_lazy('course_list')

    def test_func(self):
        return self.request.user.is_staff
    
class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'crm/course_form.html'
    success_url = reverse_lazy('course_list')

    def test_func(self):
        return self.request.user.is_staff

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Course
    template_name = 'crm/course_confirm_delete.html'
    success_url = reverse_lazy('course_list')

    def test_func(self):
        return self.request.user.is_staff

class GroupListView(LoginRequiredMixin, generic.ListView):
    model = Group
    template_name = 'crm/group_list.html'
    context_object_name = 'groups'
    paginate_by = 10

class GroupDetailView(LoginRequiredMixin, generic.DetailView):
    model = Group
    template_name = 'crm/group_detail.html'

class GroupCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'crm/group_form.html'
    success_url = reverse_lazy('group_list')

    def test_func(self):
        return self.request.user.is_staff

class ClassScheduleListView(LoginRequiredMixin, generic.ListView):
    model = ClassSchedule
    template_name = 'crm/class_schedule_list.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        if self.request.user.is_staff:
            return ClassSchedule.objects.all()
        else:
            student = Student.objects.get(user=self.request.user)
            return ClassSchedule.objects.filter(group__students=student)

class AttendanceCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'crm/attendance_form.html'
    success_url = reverse_lazy('attendance_list')

    def test_func(self):
        return self.request.user.is_staff

class AcademicProgressListView(LoginRequiredMixin, generic.ListView):
    model = AcademicProgress
    template_name = 'crm/academic_progress_list.html'
    context_object_name = 'progress_records'

    def get_queryset(self):
        if self.request.user.is_staff:
            return AcademicProgress.objects.all()
        else:
            student = Student.objects.get(user=self.request.user)
            return AcademicProgress.objects.filter(student=student)

class ExamListView(LoginRequiredMixin, generic.ListView):
    model = Exam
    template_name = 'crm/exam_list.html'
    context_object_name = 'exams'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Exam.objects.all()
        else:
            student = Student.objects.get(user=self.request.user)
            return Exam.objects.filter(course__in=student.groups.values('course'))

class PaymentListView(LoginRequiredMixin, generic.ListView):
    model = Payment
    template_name = 'crm/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all().select_related('enrollment__student', 'enrollment__course')
        else:
            student = Student.objects.get(user=self.request.user)
            return Payment.objects.filter(enrollment__student=student).select_related('enrollment__course')

@login_required
def print_invoice(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    company_info = CompanyInfo.objects.first()
    enrollment = payment.enrollment
    student = enrollment.student
    context = {
        'payment': payment,
        'company_info': company_info,
        'enrollment': enrollment,
        'student': student,
        'print_view': True,  # Añadimos esta variable para ajustar la plantilla si es necesario
    }
    return render(request, 'crm/invoice.html', context)

@login_required
def view_invoice(request, payment_id):
    # Esta función puede ser idéntica a invoice_view
    return invoice_view(request, payment_id)

@login_required
def invoice_view(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    company_info = CompanyInfo.objects.first()
    enrollment = payment.enrollment
    student = enrollment.student
    context = {
        'payment': payment,
        'company_info': company_info,
        'enrollment': enrollment,
        'student': student,
    }
    return render(request, 'crm/invoice.html', context)
      

class AnnouncementListView(LoginRequiredMixin, generic.ListView):
    model = Announcement
    template_name = 'crm/announcement_list.html'
    context_object_name = 'announcements'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Announcement.objects.all()
        else:
            student = Student.objects.get(user=self.request.user)
            return Announcement.objects.filter(courses__in=student.groups.values('course')) | Announcement.objects.filter(is_global=True)

class EnrollmentCreateView(LoginRequiredMixin, UserPassesTestMixin, generic.CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'crm/enrollment_form.html'
    success_url = reverse_lazy('enrollment_list')

    def form_valid(self, form):
        # Aquí se puede añadir cualquier lógica adicional si es necesario
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff

class EnrollmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'crm/enrollment_form.html'
    success_url = reverse_lazy('enrollment_list')

    def form_valid(self, form):
        # Lógica adicional, si es necesario
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_staff

class EnrollmentListView(LoginRequiredMixin, UserPassesTestMixin, generic.ListView):
    model = Enrollment
    template_name = 'crm/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_staff

class EnrollmentDetailView(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    model = Enrollment
    template_name = 'crm/enrollment_detail.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user == self.get_object().student.user


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Agregar depuración para ver el nombre de usuario
        print(f'Trying to authenticate user: {username}')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f'User authenticated: {username}')
            login(request, user)
            return redirect('dashboard')
        else:
            print(f'Authentication failed for user: {username}')
            
            # Mejorar los mensajes de error
            user_exists = User.objects.filter(username=username).exists()
            if user_exists:
                messages.error(request, 'Incorrect password.')
            else:
                messages.error(request, 'Username does not exist.')
    
    company_info = CompanyInfo.objects.first()
    return render(request, 'crm/login.html', {'company_info': company_info})
    

@login_required
def send_progress_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    progress = AcademicProgress.objects.filter(student=student).order_by('-date')[:5]

    subject = f"Progress Report for {student.user.get_full_name()}"
    message = f"Here's the recent progress for {student.user.get_full_name()}:\n\n"
    for p in progress:
        message += f"{p.course.name}: {p.grade}% - {p.date}\n"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [student.user.email],
        fail_silently=False,
    )

    return redirect('student_detail', pk=student.id)

@login_required
def invoice_view(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    company_info = CompanyInfo.objects.first()
    enrollment = payment.enrollment
    student = enrollment.student
    context = {
        'payment': payment,
        'company_info': company_info,
        'enrollment': enrollment,
        'student': student,
    }
    return render(request, 'crm/invoice.html', context)

def download_invoice_pdf(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    company_info = CompanyInfo.objects.first()
    enrollment = payment.enrollment
    student = enrollment.student

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=72, leftMargin=72, 
                            topMargin=72, bottomMargin=18)

    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Right', alignment=1))
    styles.add(ParagraphStyle(name='Left', alignment=0))
    styles.add(ParagraphStyle(name='Center', alignment=1))

    # Encabezado con logo y título
    logo_path = os.path.join(settings.MEDIA_ROOT, 'company_logos', 'logo-bubble.png')

    # Verificación de la existencia del archivo
    if os.path.exists(logo_path):
        logo = Image(logo_path, 1.9 * cm, 1.9 * cm)  # Ajuste del tamaño del logo
    else:
        # Manejo en caso de que el logo no se encuentre
        logo = Paragraph("Logo no disponible", styles['Normal'])

    # Nombre de la compañía
    company_name = Paragraph("<font size=16><b>Bubble English Academy</b></font>", styles['Left'])
    
    # Datos de la compañía
    company_data = Paragraph("""
    Plaza Anzaran 7, bajo, CP 20301, Irún, Guipúzcoa<br/>
    Tel: (+34) 943 255 830<br/>
    Email: info@bubbleacademy.es
    """, styles['Left'])
    
    # Crear tabla para el encabezado
    company_info_table_data = [
        [logo, company_name, ""],
        ["", company_data, Paragraph(f"<font size=14><b>FACTURA</b></font><br/>Factura n°: {payment.id}<br/>Fecha: {payment.payment_date.strftime('%d/%m/%Y')}", styles['Right'])],
    ]
    company_info_table = Table(company_info_table_data, colWidths=[3*cm, 10*cm, 6*cm])
    company_info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('TOPPADDING', (1, 1), (1, 1), 1),  # Espacio de 5px (aprox 0.14cm) entre el nombre y los datos
    ]))

    elements.append(company_info_table)
    elements.append(Spacer(1, 0.5*cm))

    # Información del cliente
    elements.append(Paragraph("<b>Cliente</b>", styles['Left']))
    client_data = [
        [Paragraph(student.user.get_full_name(), styles['Left'])],
        [Paragraph(student.address, styles['Left'])],
        [Paragraph(f"Email: {student.user.email}", styles['Left'])]
    ]
    client_table = Table(client_data)
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.5*cm))

    # Detalles de la factura
    data = [
        ['Artículo', 'Cantidad', 'Precio Unitario', 'Total'],
        [enrollment.course.name, '1', f'€{enrollment.total_cost:.2f}', f'€{enrollment.total_cost:.2f}'],
    ]
    table = Table(data, colWidths=[9*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.7, 0.8, 0.8)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROUNDEDCORNERS', [5, 5, 5, 5]),
    ]))
    elements.append(table)

    # Totales
    subtotal = enrollment.total_cost
    vat = enrollment.total_cost_with_vat - enrollment.total_cost
    total = enrollment.total_cost_with_vat

    totals_data = [
        ['', '', 'Subtotal:', f'€{subtotal:.2f}'],
        ['', '', f'IVA ({enrollment.vat_rate:.2f}%):', f'€{vat:.2f}'],
        ['', '', 'Total:', f'€{total:.2f}'],
    ]
    totals_table = Table(totals_data, colWidths=[9*cm, 3*cm, 3*cm, 3*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (2, 0), (3, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 0), (3, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (2, 2), (3, 2), 1, colors.black),
    ]))
    elements.append(totals_table)
    
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(f"Método de pago: {payment.get_payment_method_display()}", styles['Left']))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("¡Gracias por su confianza!", styles['Center']))

    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'factura_{payment.id}.pdf')

class ChangePasswordView(PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'crm/change_password.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
class CustomPasswordResetView(PasswordResetView):
    template_name = 'crm/password_reset_form.html'
    email_template_name = 'crm/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        active_users = User.objects.filter(email__iexact=email, is_active=True)
        if not active_users.exists():
            # No user with this email exists
            messages.error(self.request, "No existe un usuario activo con este correo electrónico. Por favor, verifica e intenta nuevamente.")
            return render(self.request, self.template_name, {'form': form})
        
        # If user exists, proceed with password reset
        return super().form_valid(form)

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'crm/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'crm/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        user = form.save()
        
        # Verificar que la contraseña se ha cambiado
        new_password = form.cleaned_data['new_password1']
        if user.check_password(new_password):
            logger.info(f"Contraseña cambiada con éxito para el usuario: {user.username}")
            messages.success(self.request, "Tu contraseña ha sido cambiada con éxito.")
            
            # Intentar actualizar el email del estudiante si existe
            try:
                student = user.student
                student.email = user.email
                student.save()
            except ObjectDoesNotExist:
                logger.info(f"Usuario {user.username} no tiene perfil de estudiante asociado.")
        else:
            logger.error(f"La contraseña no se cambió correctamente para el usuario: {user.username}")
            messages.error(self.request, "Hubo un problema al cambiar tu contraseña. Por favor, inténtalo de nuevo.")
        
        # Actualizar la sesión para mantener al usuario conectado
        update_session_auth_hash(self.request, form.user)
        
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.error(f"Formulario inválido: {form.errors}")
        messages.error(self.request, "Hubo un problema al cambiar tu contraseña. Por favor, inténtalo de nuevo.")
        return super().form_invalid(form)

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'crm/password_reset_complete.html'