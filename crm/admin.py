from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse, path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import PermissionDenied
from django.utils.html import escape
from django.utils.http import unquote  # Asegúrate de que esta línea esté presente
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import transaction
from django.utils.html import format_html
from .models import (
    Student, FamilyMember, Teacher, Course, Group, ClassSchedule,
    Attendance, AcademicProgress, Exam, ExamResult, Announcement, Enrollment,
    CompanyInfo, Payment
)
from .forms import UserChangePasswordForm, PaymentForm, CompanyInfoForm

# Forms
class StudentAdminForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Student
        fields = ['user', 'first_name', 'last_name', 'email', 'date_of_birth', 'address', 'emergency_contact', 'level', 'document_type', 'document_number', 'nationality', 'profile_photo']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

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

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'masked_password')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

    def masked_password(self, obj):
        return format_html('<span style="color: #999;">*********</span>')
    masked_password.short_description = 'Password'

    def get_urls(self):
        from django.urls import path
        return [
            path(
                '<id>/password/',
                self.admin_site.admin_view(self.user_change_password),
                name='auth_user_password_change',
            ),
        ] + super().get_urls()

    def user_change_password(self, request, id, form_url='', extra_context=None):
        user = self.get_object(request, unquote(id))
        if not self.has_change_permission(request, user):
            raise PermissionDenied
        if user is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
                'name': self.model._meta.verbose_name,
                'key': escape(id),
            })
        if request.method == 'POST':
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, user, change_message)
                msg = _('Password changed successfully.')
                messages.success(request, msg)
                update_session_auth_hash(request, form.user)
                return HttpResponseRedirect(
                    reverse(
                        '%s:%s_%s_change' % (
                            self.admin_site.name,
                            user._meta.app_label,
                            user._meta.model_name,
                        ),
                        args=(user.pk,),
                    )
                )
        else:
            form = AdminPasswordChangeForm(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % escape(user.get_username()),
            'adminForm': adminForm,
            'form_url': form_url,
            'form': form,
            'is_popup': (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
        }
        context.update(extra_context or {})

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.change_user_password_template or
            'admin/auth/user/change_password.html',
            context,
        )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 1

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentAdminForm
    list_display = (
        'user', 'get_full_name', 'age', 'get_email', 'date_of_birth', 'address',
        'emergency_contact', 'level', 'document_type', 'document_number',
        'nationality', 'profile_photo', 'get_groups'
    )
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    inlines = [FamilyMemberInline]
    readonly_fields = ('get_full_name', 'age', 'get_email')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Nombre Completo'

    def age(self, obj):
        return obj.age
    age.short_description = 'Edad'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Grupo'

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    readonly_fields = ('amount', 'payment_date', 'payment_method', 'is_confirmed')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'group', 'start_date', 'total_cost', 'total_cost_with_vat')
    inlines = [PaymentInline]

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Solo para nuevos Enrollments
            try:
                Payment.objects.create(
                    enrollment=obj,
                    amount=obj.total_cost_with_vat,
                    payment_method='cash'
                )
            except Exception as e:
                self.message_user(request, f"Error al crear el pago: {str(e)}", level='ERROR')
                raise  # Re-lanza la excepción para revertir la transacción

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'amount', 'payment_method', 'is_confirmed', 'invoice_link')

    def payment_method(self, obj):
        return obj.get_payment_method_display()
    payment_method.short_description = 'Payment Method'

    def invoice_link(self, obj):
        url = reverse('invoice_view', args=[obj.id])
        return format_html('<a href="{}">Ver Factura</a>', url)
    invoice_link.short_description = 'Factura'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'start_date', 'end_date', 'max_students')
    list_filter = ('level', 'start_date')
    search_fields = ('name', 'description')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'specialization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'teacher')
    list_filter = ('course', 'teacher')
    search_fields = ('name', 'course__name', 'teacher__user__username')

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'day_of_week', 'start_time', 'end_time', 'room')
    list_filter = ('day_of_week', 'group')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_schedule', 'date', 'is_present')
    list_filter = ('is_present', 'date', 'class_schedule')
    search_fields = ('student__user__username', 'class_schedule__group__name')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'date', 'duration', 'max_score')
    list_filter = ('course', 'date')
    search_fields = ('name', 'course__name')

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score')
    list_filter = ('exam', 'score')
    search_fields = ('student__user__username', 'exam__name')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_posted', 'is_global')
    list_filter = ('is_global', 'date_posted', 'courses')
    search_fields = ('title', 'content')

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'fiscal_number', 'phone', 'email', 'display_logo')
    readonly_fields = ('display_logo',)

    def display_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="100" />', obj.logo.url)
        return "No logo"
    display_logo.short_description = 'Logo'