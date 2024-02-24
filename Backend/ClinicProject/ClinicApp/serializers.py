
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import Medicine, MedicinePrice, Vendor, User, Doctor, Department, Employee, UserRole, Patient, Appointment, \
    Confirmation, HealthRecord, Service, MedicineDetails, Instruction, ReceiptDetail, Receipt, Nurse
from dateutil import parser

#Dynamid
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
#MEDICINE
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
        fields = ['id', 'first_name', 'last_name', 'email' , 'birthdate', 'gender', 'address', 'avatar', 'image_url', 'username', 'password', 'role']

    def create(self, validated_data):
        u = User(**validated_data)
        u.set_password(validated_data['password'])
        u.role = UserRole.BENH_NHAN if 'role' not in validated_data.keys() else validated_data['role']
        u.save()
        if u.role == UserRole.BENH_NHAN:
            p = Patient(user_info=u)
            p.save()
        else:
            e = Employee(user_info=u)
            e.save()
            if u.role == UserRole.BAC_SI:
                d = Doctor(employee_info=e)
                d.save()
            else:
                n = Nurse(employee_info=e)
                n.save()

        return u


class UserListSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'image_url']
class EmployeeSerializer(DynamicFieldsModelSerializer):
    user_info = UserSerializer()

    class Meta:
        model = Employee
        fields = "__all__"
class EmployeeListSerializer(ModelSerializer):
    user_info = UserListSerializer()
    class Meta:
        model = Employee
        fields = ['user_info']

class DepartmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class DoctorSerializer(DynamicFieldsModelSerializer):
    departments = DepartmentSerializer(fields=['id', 'name'])
    employee_info = EmployeeSerializer()

    class Meta:
        model = Doctor
        fields = ['employee_info', 'departments']

class DoctorListSerializer(ModelSerializer):
    employee_info = EmployeeListSerializer()
    departments = DepartmentSerializer(fields=['id', 'name'])
    class Meta:
        model = Doctor
        fields = ['employee_info', 'departments']


class NurseSerializer(DynamicFieldsModelSerializer):
    employee_info = EmployeeSerializer()
    class Meta:
        model = Doctor
        fields = ['employee_info']
class PatientSerializer(DynamicFieldsModelSerializer):
    user_info = UserSerializer()
    class Meta:
        model = Patient
        fields = "__all__"


class PatientListSerializer(ModelSerializer):
    user_info = UserListSerializer()
    class Meta:
        model = Patient
        fields = ['user_info']

class NonDetailEmployeeSerializer(DynamicFieldsModelSerializer):
    doctor_info = DoctorSerializer(fields=['departments'])
    nurse_info = NurseSerializer(fields=[])
    class Meta:
        model = Employee
        fields = "__all__"
#APPOINTMENT
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

    def to_internal_value(self, value):

        value['ExpectedDate'] = parser.parse(value['ExpectedDate'])
        print(value)
        return super().to_internal_value(value)

class AppointmentListSerializer(ModelSerializer):
    ExpectedDate=serializers.DateTimeField(format="%d-%m-%Y %H:%M")
    department= DepartmentSerializer()
    patient = PatientListSerializer()

    class Meta:
        model = Appointment
        fields = ['id', 'department', 'patient', 'ExpectedDate', "created_date", "confirmed"]

#HealthRecord
class ServiceSerializer(ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']

class InstructionSerializer(ModelSerializer):
    class Meta:
        model = Instruction
        fields = ['amount', 'unit', 'period']

class MedicineDetailSerializer(ModelSerializer):
    instructions = InstructionSerializer(many=True)
    medicine = MedicineListSerializer()
    class Meta:
        model = MedicineDetails
        fields = ["medicine", 'amount', 'unit', 'total', 'instructions']

class HealthRecordSerializer(ModelSerializer):
    services = ServiceSerializer(many=True)
    patient = PatientListSerializer()
    doctor = DoctorListSerializer()
    medicines_detail = MedicineDetailSerializer(many=True)
    class Meta:
        model = HealthRecord
        fields = ['id', 'patient', 'doctor', 'symstoms','overview', 'medicines_detail', 'services', 'active']

class HealthRecordListSerializer(ModelSerializer):
    patient = PatientListSerializer()
    doctor = DoctorListSerializer()

    class Meta:
        model = HealthRecord
        fields = ['id', 'patient', 'doctor', 'created_date']

#Receipt
class ReceiptDetailSerializer(ModelSerializer):
    class Meta:
        model = ReceiptDetail
        fields = ['name', 'price']
class ReceiptSerializer(DynamicFieldsModelSerializer):
    record = HealthRecordListSerializer()
    detail = ReceiptDetailSerializer(many=True)
    class Meta:
        model = Receipt
        fields = '__all__'
