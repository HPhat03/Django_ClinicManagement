from datetime import date

from django.db import models
from django.contrib.auth.models import AbstractUser
from django_enumfield import enum
# Create your models here.

#enum
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
#model
class BaseModel(models.Model):
    class Meta:
        abstract = True


    id = models.IntegerField(primary_key=True)
    created_date = models.DateField(auto_now_add=True)
    updated_date = models.DateField(auto_now=True)
    active = models.BooleanField(default=True)
class User(AbstractUser):
    birthdate = models.DateField(null=False, default=date(2024, 1, 1))
    address = models.CharField(max_length=100, null=False, default='ABC')
    gender = models.BooleanField(null=False, default=True)
    avatar = models.ImageField(upload_to='users/%Y/%m', null=True)
    role = enum.EnumField(UserRole, default=UserRole.BENH_NHAN)

class Patient(models.Model):
    user_info = models.OneToOneField(User, related_name="patient_info",
                                     on_delete=models.CASCADE, parent_link=True,
                                     null=False, primary_key=True)
class Employee(models.Model):
    user_info = models.OneToOneField(User, related_name= "employee_info",
                                     on_delete=models.CASCADE, parent_link=True,
                                     null=False, primary_key=True)
    diploma = models.TextField()

class Doctor(models.Model):
    employee_info = models.OneToOneField(Employee, related_name="doctor_info",
                                         on_delete=models.CASCADE, parent_link=True,
                                         null=False, primary_key=True)
    departments = models.ManyToManyField('Department', related_name="doctors")

class Nurse(models.Model):
    employee_info = models.OneToOneField(Employee, related_name="nurse_info",
                                         on_delete=models.CASCADE, parent_link=True,
                                         null=False, primary_key=True)
class Schedule(BaseModel):
    class Meta:
        unique_together = ('ScheduleDate', 'department')

    ScheduleDate = models.DateField(null=False)
    department = models.ForeignKey('Department',on_delete=models.CASCADE, related_name='schedules')
    employees = models.ManyToManyField(Employee,related_name='schedules')
class Department(BaseModel):
    name = models.CharField(max_length=50, null=False)

    def __str__(self):
        return self.name

class Appointment(BaseModel):
    ExpectedDate = models.DateTimeField(null=False)
    department = models.ForeignKey(Department,on_delete=models.SET_NULL, related_name="appointments", null=True)
    patient = models.ForeignKey(Patient,on_delete=models.CASCADE, related_name="appointments", null=False)

class Confirmation(models.Model):
    appointment = models.OneToOneField(Appointment,on_delete=models.CASCADE, related_name="confirmation", null=False, parent_link=True, primary_key=True)
    nurse = models.ForeignKey(Nurse, on_delete=models.SET_NULL, related_name="confirmation", null=True)
    date = models.DateTimeField(auto_now_add=True)

class HealthRecord(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="health_records", null=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="health_records", null=False)
    symstoms = models.TextField(null=False)
    paid = models.BooleanField(null=False, default=False)
    medicines = models.ManyToManyField('Medicine', related_name='records', through='MedicineDetails')


class MedicineDetails(BaseModel):
    health_record = models.ForeignKey(HealthRecord, on_delete=models.CASCADE,
                                      null=False)
    medicine = models.ForeignKey('Medicine', on_delete=models.CASCADE,
                                      null=False)
    amount = models.FloatField(null=False)
    unit = enum.EnumField(Unit, default=Unit.TABLET)

class Instruction(BaseModel):
    medicine = models.ForeignKey(MedicineDetails, on_delete=models.CASCADE,
                                 null=False)
    amount = models.FloatField(null=False)
    unit = enum.EnumField(Unit, default=Unit.TABLET)
    period = enum.EnumField(Period, default=Period.MORN)



class Medicine(BaseModel):
     name = models.CharField(max_length=100, null=False)
     vendor = models.ForeignKey('Vendor', on_delete=models.SET_NULL, related_name="medicines", null=True)
     content = models.TextField()
     image = models.ImageField(upload_to='medicines/%Y/%m')


class MedicinePrice(BaseModel):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="prices", null=False)
    unit = enum.EnumField(Unit, default=Unit.BOX)
    unit_price = models.IntegerField()

class Vendor(BaseModel):
    name = models.CharField(max_length=100, null=False)
    address = models.CharField(max_length=100)

    def __str__(self):
        return self.name