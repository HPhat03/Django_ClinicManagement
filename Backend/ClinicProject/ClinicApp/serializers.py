
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import Medicine, MedicinePrice, Vendor, User, Doctor, Department, Employee, UserRole, Patient, Appointment, \
    Confirmation


class MedicinePriceSerializer(ModelSerializer):
    class Meta:
        model = MedicinePrice
        fields = ['id', 'created_date', 'unit', 'unit_price']

class VendorSerializer(ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'address']


class MedicineSerializer(ModelSerializer):
    prices = MedicinePriceSerializer(many=True)
    vendor = VendorSerializer()
    vendor = VendorSerializer()
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'vendor', 'content', 'image_url', 'prices']

class MedicineListSerializer(ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'image_url']



#USER
class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email' , 'birthdate', 'gender', 'address', 'avatar', 'username', 'password', 'role']

    def create(self, validated_data):
        u = User(**validated_data)
        u.set_password(validated_data['password'])
        u.role = UserRole.BENH_NHAN
        u.save()

        p = Patient(user_info=u)
        p.save()

        return u


class UserListSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'image_url']
class EmployeeSerializer(ModelSerializer):
    user_info = UserSerializer()
    class Meta:
        model = Employee
        fields = ['user_info', 'diploma']
class EmployeeListSerializer(ModelSerializer):
    user_info = UserListSerializer()
    class Meta:
        model = Employee
        fields = ['user_info']

class DepartmentSerializer(ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']

class DoctorSerializer(ModelSerializer):
    departments = DepartmentSerializer()
    employee_info = EmployeeSerializer()
    class Meta:
        model = Doctor
        fields = ['employee_info', 'departments']

class DoctorListSerializer(ModelSerializer):
    employee_info = EmployeeListSerializer()
    departments = DepartmentSerializer()
    class Meta:
        model = Doctor
        fields = ['employee_info', 'departments']

#APPOINTMENT
class PatientListSerializer(ModelSerializer):
    user_info = UserListSerializer()
    class Meta:
        model = Patient
        fields = ['user_info']
class ConfirmationSerializer(ModelSerializer):
    class Meta:
        model = Confirmation
        fields = '__all__'

class AppointmentSerializer(ModelSerializer):
    ExpectedDate=serializers.DateTimeField(format="%d-%m-%Y %H:%M")
    department = DepartmentSerializer()
    patient = PatientListSerializer()
    confirmation=ConfirmationSerializer()
    class Meta:
        model = Appointment
        fields ='__all__'

class AppointmentListSerializer(ModelSerializer):
    ExpectedDate=serializers.DateTimeField(format="%d-%m-%Y %H:%M")
    # department= DepartmentSerializer()
    # patient = PatientListSerializer()

    class Meta:
        model = Appointment
        fields = ['id', 'department', 'patient', 'ExpectedDate', "created_date", "confirmed"]
