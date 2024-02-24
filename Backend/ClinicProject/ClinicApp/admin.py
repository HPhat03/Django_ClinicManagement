from admin_reorder.middleware import ModelAdminReorder
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
from django.utils.safestring import mark_safe

from .models import Doctor, Nurse, Schedule, Medicine, Vendor, MedicinePrice, Department, Employee, User, UserRole, \
    Patient, Service
from nested_inline.admin import NestedStackedInline, NestedModelAdmin

from django.conf import settings
# Register your models here.

#ADMIN PAGE SETUP
class myAdminPage(admin.AdminSite):
    site_header = "PB CLINIC ADMIN"

#INLINE ADMIN CLASS
class PriceInlineAdmin(NestedStackedInline):
    model = MedicinePrice
    fk_name = 'medicine'
    extra = 1
    show_change_link = True
class MedicineInlineAdmin(NestedStackedInline):
    model = Medicine
    fk_name = 'vendor'
    extra = 1
    inlines = [PriceInlineAdmin,]
    readonly_fields = ['image_of_medicine']

    def image_of_medicine(self, obj):
        return mark_safe(
            f"<img src='{obj.image.url}' width=250/>"
        )

#CKEDITOR FORM
class MedicineForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget)
    class Meta:
        model = Medicine
        fields = '__all__'
#ADMIN CLASS
class DepartmentAdmin(admin.ModelAdmin):
    pass
class VendorAdmin(NestedModelAdmin):
    model = Vendor
    inlines = [MedicineInlineAdmin]

class MedicineAdmin(admin.ModelAdmin):
    form = MedicineForm
    list_display = ['id', 'name','vendor', 'active']
    list_filter = ['vendor', 'active']
    inlines = [PriceInlineAdmin]
    search_fields = ['name']
    readonly_fields = ['image_of_medicine']

    def image_of_medicine(self, obj):
        return mark_safe(
            f"<img src='{obj.image.url}' width=250/>"
        )
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','Gender', 'role', 'is_active']
    list_filter = ('role',)
    search_fields = ('last_name', 'first_name')
    readonly_fields = ['Gender','image', 'password', 'username']
    exclude = ['groups', 'user_permissions', 'gender', 'is_staff', 'is_superuser']
    def image(self, obj):
        return mark_safe(
            f"<img src='{obj.avatar.url}' width=150/>"
        )
    def Gender(self, obj):
        return "Nam" if obj.gender else "Nữ"

    def get_queryset(self, request):
        q = super().get_queryset(request)
        return q.filter(Q(role = UserRole.BAC_SI) | Q(role=UserRole.Y_TA)).order_by('role')
    def save_model(self, request, obj, form, change):
        obj.password = make_password(obj.password.strip())
        super().save_model(request, obj, form, change)
        if obj.role == UserRole.BENH_NHAN:
            temp = Patient(user_info=obj)
            temp.save()
        else:
            temp = Employee(user_info=obj)
            temp.save()
            match obj.role:
                case UserRole.BAC_SI:
                    tempDoc = Doctor(employee_info=temp)
                    tempDoc.save()
                    print(tempDoc.employee_info)
                case UserRole.Y_TA:
                    tempNurse = Nurse(employee_info=temp)
                    tempNurse.save()


class HRAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

class EmployeeAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        return {}
class EmployeeInlineAdmin(admin.StackedInline):
    model = Schedule.employees.through
    extra = 1


class ScheduleAdmin(admin.ModelAdmin):
    class Media:
        js = ('/static/js/script.js',)

    list_display = ['id', 'department', 'ScheduleDate', 'created_date', 'active']
    list_filter = ('department',)
    inlines = [EmployeeInlineAdmin, ]
    exclude = ['employees']

    def get_queryset(self, request):
        q = super().get_queryset(request)
        return q.order_by('-ScheduleDate')

    def save_formset(self, request, form, formset, change):
        formset.save()
        for fs in formset:
            t = fs.instance.employee
            if t.user_info.role == UserRole.BAC_SI :
                if form.instance.department != t.doctor_info.departments:
                    fs.instance.delete()
                    msg = f'Không thể xếp bác sĩ khoa khác vào {form.instance.department}'
                    messages.add_message(request, level=messages.ERROR, message=msg)

admin_site = myAdminPage(name="admin_site")
# admin_site = admin.site
admin_site.register(Doctor, HRAdmin)
admin_site.register(Nurse, HRAdmin)
admin_site.register(Schedule, ScheduleAdmin)
admin_site.register(Vendor, VendorAdmin)
admin_site.register(Medicine, MedicineAdmin)
admin_site.register(Department, DepartmentAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(Employee, EmployeeAdmin)
#new
admin_site.register(Service)


#firmware
class Reorder(ModelAdminReorder):
    def init_config(self, request, app_list):
        self.request = request
        self.app_list = app_list

        self.config = getattr(settings, 'ADMIN_REORDER', None)
        if not self.config:
            # ADMIN_REORDER settings is not defined.
            raise ImproperlyConfigured('ADMIN_REORDER config is not defined.')

        if not isinstance(self.config, (tuple, list)):
            raise ImproperlyConfigured(
                'ADMIN_REORDER config parameter must be tuple or list. '
                'Got {config}'.format(config=self.config))

        admin_index = admin_site.index(request)
        try:
            # try to get all installed models
            app_list = admin_index.context_data['app_list']
        except KeyError:
            # use app_list from context if this fails
            pass

        # Flatten all models from apps
        self.models_list = []
        for app in app_list:
            for model in app['models']:
                model['model_name'] = self.get_model_name(
                    app['app_label'], model['object_name'])
                self.models_list.append(model)
