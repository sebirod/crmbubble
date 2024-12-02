from django.urls import path
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from .views import ChangePasswordView, CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # Rutas para estudiantes
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('students/create/', views.StudentCreateView.as_view(), name='student_create'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_update'),
    
    # Rutas para cursos
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    
    # Rutas para grupos
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group_create'),
    
    # Rutas para horarios de clases
    path('schedules/', views.ClassScheduleListView.as_view(), name='class_schedule_list'),
    
    # Rutas para asistencia
    path('attendance/create/', views.AttendanceCreateView.as_view(), name='attendance_create'),
    
    # Rutas para progreso académico
    path('progress/', views.AcademicProgressListView.as_view(), name='academic_progress_list'),
    
    # Rutas para exámenes
    path('exams/', views.ExamListView.as_view(), name='exam_list'),
    
    # Rutas para pagos
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('print-invoice/<int:payment_id>/', views.print_invoice, name='print_invoice'),
    path('view-invoice/<int:payment_id>/', views.view_invoice, name='view_invoice'),
    
    # Rutas para anuncios
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    
    # Rutas para reportes y facturación
    path('send-progress-report/<int:student_id>/', views.send_progress_report, name='send_progress_report'),
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('enrollments/create/', views.EnrollmentCreateView.as_view(), name='enrollment_create'),
    path('enrollments/<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment_detail'),
    path('enrollments/<int:pk>/edit/', views.EnrollmentUpdateView.as_view(), name='enrollment_update'),
    path('invoice/<int:payment_id>/', views.invoice_view, name='invoice_view'),
    path('download-invoice-pdf/<int:payment_id>/', views.download_invoice_pdf, name='download_invoice_pdf'),
    
    # Ruta para cambiar la contraseña desde admin
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # Ruta para cambiar la contraseña desde usuario
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

# Agregar el manejo de archivos estáticos en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

