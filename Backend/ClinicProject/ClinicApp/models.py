import datetime
from datetime import date


from django.db import models
from django.contrib.auth.models import AbstractUser
from django_enumfield import enum


from cloudinary.models import CloudinaryField

from ckeditor.fields import RichTextField
# Create your models here.

# enum
class UserRole(enum.Enum):
    BAC_SI = 0
    Y_TA = 1
    ADMIN = 2
    BENH_NHAN = 3


class Unit(enum.Enum):
    TABLET = 0
    PACK = 1
    BOX = 2


class Period(enum.Enum):
    MORN = 0
    AFNOON = 1
    EVE = 2


# model
class BaseModel(models.Model):
    class Meta:
        abstract = True

    id = models.AutoField(primary_key=True)
    created_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    active = models.BooleanField(default=True)


class User(AbstractUser):
    birthdate = models.DateField(null=False, default=date(2024, 1, 1))
    address = models.CharField(max_length=100, null=False, default='ABC')
    gender = models.BooleanField(null=False, default=True)
    avatar = CloudinaryField('image', default= None, null=True)
    role = enum.EnumField(UserRole, default=UserRole.ADMIN)

    @property
    def name(self):
        return self.last_name + ' ' + self.first_name

    @property
    def image_url(self):
        return self.avatar.url


class Patient(models.Model):
    user_info = models.OneToOneField(User, related_name="patient_info",
                                     on_delete=models.CASCADE,
                                     null=False, primary_key=True)


class Employee(models.Model):
    user_info = models.OneToOneField(User, related_name="employee",
                                     on_delete=models.CASCADE,
                                     null=False, primary_key=True, editable=False)
    diploma = RichTextField()
    def __str__(self):
        role = self.user_info.role
        S = ''
        O = ''

        match role:
            case UserRole.BAC_SI:
                S = 'Bác sĩ'
                O = f' - {self.doctor_info.departments}'
            case UserRole.Y_TA:
                S = 'Y tá'
                O = ""

        text = S + ' ' + self.user_info.name
        tab = (30 - len(text)) * "_" if role == UserRole.BAC_SI else ""
        return  f'{text}{tab}{O}'


class Doctor(models.Model):
    employee_info = models.OneToOneField(Employee, related_name="doctor_info",
                                         on_delete=models.CASCADE,
                                         null=False, primary_key=True, editable=False)
    departments = models.ForeignKey('Department', related_name="doctors",null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.employee_info.user_info.name
class Nurse(models.Model):
    employee_info = models.OneToOneField(Employee, related_name="nurse_info",
                                         on_delete=models.CASCADE,
                                         null=False, primary_key=True, editable=False)

    def __str__(self):
        return self.employee_info.user_info.name


class Schedule(BaseModel):
    class Meta:
        unique_together = ('ScheduleDate', 'department')

    ScheduleDate = models.DateField(null=False)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='schedules')
    employees = models.ManyToManyField(Employee, related_name='schedules')

    def __str__(self):
        return f"{self.department} - {self.ScheduleDate}"
class Department(BaseModel):
    name = models.CharField(max_length=50, null=False)

    def __str__(self):
        return self.name


class Appointment(BaseModel):
    class Meta:
        unique_together = ('patient', 'ExpectedDate')
    ExpectedDate = models.DateTimeField(null=False, default=datetime.datetime.now())
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, related_name="appointments", null=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments", null=False)
    confirmed = models.BooleanField(null=False, default=False)

class Confirmation(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="confirmation", null=False,
                                       primary_key=True)
    nurse = models.ForeignKey(Nurse, on_delete=models.SET_NULL, related_name="appointment_confirmed", null=True)
    date = models.DateTimeField(auto_now_add=True)

class Service(BaseModel):
    name = models.CharField(max_length=100, null=False)
    price = models.IntegerField(null=False)


class HealthRecord(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="health_records", null=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="health_records", null=False)
    symstoms = models.TextField(null=False)
    overview = models.TextField(null=True, default=None)
    locked = models.BooleanField(null=False, default=False)
    medicines = models.ManyToManyField('Medicine', related_name='records', through='MedicineDetails')
    services = models.ManyToManyField(Service, related_name='records')

class Receipt(models.Model):
    record = models.OneToOneField(HealthRecord, on_delete=models.CASCADE, related_name='receipt', primary_key=True)
    nurse = models.ForeignKey(Nurse,related_name='receipt_confirmed', on_delete=models.SET_NULL, null=True)
    total = models.IntegerField()
    created_date = models.DateField(default=date.today(),)
    paid = models.BooleanField(null=False, default=False)

class ReceiptDetail(models.Model):
    id = models.AutoField(primary_key=True)
    receipt = models.ForeignKey(Receipt, related_name="detail", on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=100)
    price = models.IntegerField(default=0)
class MedicineDetails(BaseModel):
    class Meta:
        unique_together = ("health_record", "medicine")
    health_record = models.ForeignKey(HealthRecord, on_delete=models.CASCADE,
                                      null=False, related_name='medicines_detail')
    medicine = models.ForeignKey('Medicine', on_delete=models.CASCADE,
                                 null=False)
    amount = models.FloatField(null=False)
    unit = enum.EnumField(Unit, default=Unit.TABLET)
    total = models.IntegerField()
    instructions = models.ManyToManyField('Instruction', related_name="medicine")


class Instruction(BaseModel):
    amount = models.FloatField(null=False)
    unit = enum.EnumField(Unit, default=Unit.TABLET)
    period = enum.EnumField(Period, default=Period.MORN)


class Medicine(BaseModel):
    name = models.CharField(max_length=100, null=False)
    vendor = models.ForeignKey('Vendor', on_delete=models.SET_NULL, related_name="medicines", null=True)
    content = RichTextField()
    image = CloudinaryField('image')

    @property
    def image_url(self):
        return self.image.url
    def __str__(self):
        return self.name

class MedicinePrice(BaseModel):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="prices", null=False)
    unit = enum.EnumField(Unit, default=Unit.BOX)
    unit_price = models.IntegerField()

    def __str__(self):
        return f"Price by {self.unit}"


class Vendor(BaseModel):
    name = models.CharField(max_length=100, null=False)
    address = models.CharField(max_length=100)

    def __str__(self):
        return self.name


