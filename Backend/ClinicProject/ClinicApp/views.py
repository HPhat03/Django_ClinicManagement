import datetime

from django.conf import settings
from django.http import HttpResponse, request
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet, generics

from .models import Medicine, User, Employee, Doctor, UserRole, Appointment, Confirmation, HealthRecord, Service, \
    MedicineDetails, Instruction, Patient
from .serializers import MedicineSerializer, UserSerializer, DoctorSerializer, \
    MedicineListSerializer, DoctorListSerializer, AppointmentSerializer, AppointmentListSerializer, \
    HealthRecordSerializer, PatientListSerializer, PatientSerializer, InstructionSerializer, NurseSerializer
from .pagination import MedicinePagnigation

from django.core.mail import send_mail

#MESSAGE
success = {"status": "success", "message": "Thanh cong"}
failed = {"status":"failed", "message": "That Bai"}
#OTHER
Limit_appointment = 2
# Create your views here.

def test(request):
    return HttpResponse("Hello")


class MedicineViewSet(ViewSet, generics.RetrieveAPIView, generics.ListAPIView):

    queryset = Medicine.objects.filter(active=True)
    serializer_class = MedicineSerializer
    pagination_class = MedicinePagnigation
    def get_queryset(self):
        q = self.queryset
        kw = self.request.query_params.get('kw')
        if kw:
            q = q.filter(name__icontains=kw)
        return q
    def get_serializer_class(self):
        if self.action == 'list':
            s = MedicineListSerializer
        else:
            s = MedicineSerializer
        return s

class DoctorViewSet(ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            s = DoctorListSerializer
        else:
            s = DoctorSerializer
        return s

class UserViewSet(ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, ]

    def initialize_request(self, request, *args, **kwargs):

        request = super().initialize_request(request, *args, **kwargs)
        print(request.method)
        if request.method in ['POST']:
            request.parsers = [MultiPartParser(),]
        else:
            request.parsers = []

        self.action = self.action_map.get(request.method.lower())
        return request
    @action(methods=['get'], detail=False)
    def current_user(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            queryset = request.user
            data = {
                'user_info': self.serializer_class(queryset, context={"request": request}).data,
            }
            obj = {}
            if queryset.role == UserRole.BENH_NHAN:
                queryset = queryset.patient_info
                obj = PatientSerializer(queryset, context={'request': request}).data
                del obj['user_info']
            elif queryset.role == UserRole.BAC_SI:
                queryset = queryset.employee.doctor_info
                obj = DoctorSerializer(queryset, context={'request': request}).data
                del obj['employee_info']['user_info']
            elif queryset.role == UserRole.Y_TA:
                queryset = queryset.employee.nurse_info
                obj = NurseSerializer(queryset, context={'request': request}).data
                del obj['employee_info']['user_info']
            data['further_info'] = obj
            return Response(data, status=status.HTTP_200_OK)
        else:
            msg = failed.copy()
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)


class AppointmentViewSet(ViewSet,generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Appointment.objects.filter(active=True)
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            s = AppointmentListSerializer
        else:
            s = AppointmentSerializer
        return s
    def create(self, request, *args, **kwargs):
        reg_date =  datetime.datetime.strptime(request.data['ExpectedDate'], '%d-%m-%Y %H:%M')
        amount = Appointment.objects.filter(ExpectedDate__date=reg_date.date(), active=True).count()
        if amount >= Limit_appointment:
            msg = failed
            msg['message'] = f"Số lượng lịch đặt khám ngày {reg_date.date()} đã đầy, Xin vui lòng đặt lại lịch của bạn vào ngày khác"
        else:
            validated_data = {
                "ExpectedDate": reg_date,
                "department_id": request.data['department_id'],
                'patient_id': request.user.id
            }
            try:
                apm = Appointment(**validated_data)
                apm.save()
            except Exception as exc:
                msg = failed.copy()
                msg['message'] = f"lịch đặt khám ngày {reg_date} đã trùng, Xin vui lòng đặt lại lịch của bạn vào thời điểm khác"
            else:
                msg = self.serializer_class(apm, context={"request": request}).data
        return Response(msg, status=status.HTTP_200_OK)
    @action(methods=['put'], detail=True, name="Cancel this appointment", url_name='cancel', url_path="cancel")
    def cancel(self, request, pk=None):
        apm = Appointment.objects.get(pk=pk)
        if apm.patient_id == request.user.id:
            apm.active = False
            apm.save()
            msg = success.copy()
        else:
            msg = failed.copy()
            msg['message'] = "Ban khong the huy"
        return Response(msg, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, name="Confirm this appointment", url_name='confirm', url_path='confirm')
    def confirm(self, request, pk=None):
        apm = Appointment.objects.get(pk=pk)
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để xác nhận lịch khám này."
        if request.user.role == UserRole.Y_TA:
            try:
                temp = Confirmation(appointment=apm, nurse_id = request.user.id)
                temp.save()
            except Exception as exc:
                msg['message'] = str(exc)
            else:
                apm.confirmed = True
                apm.save()
                msg = self.serializer_class(apm, context={"request": request}).data
                patient = apm.patient.user_info
                t = send_mail(
                    subject="XÁC NHẬN ĐẶT LỊCH KHÁM TẠI PB CLINIC",
                    message= f'''
                Xác nhận đặt lịch khám thành công tại PB Clinic, chi tiết lịch khám:
                    Người dùng: {patient.name}.
                    Giới tính: {"Nam" if patient.gender else "Nữ"}.
                    Ngày sinh: {patient.birthdate}.
                    Địa chỉ: {patient.address}.
                Thông tin lịch khám:
                    Ngày khám: {apm.ExpectedDate.strftime('%d-%m-%Y')}.
                    Giờ dự kiến: {apm.ExpectedDate.strftime('%H:%M')}.
                    Khoa: {apm.department.name}.
                Mọi thắc mắc xin vui lòng liên hệ: **********
                PB Clinic xin cảm ơn quý khách đã sử dụng dịch vụ.
            ''',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list= [patient.email]
                )
                print(t)
        return Response(msg, status=status.HTTP_200_OK)

class HealthRecordViewSet(ViewSet, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = HealthRecord.objects.filter(active=True)
    serializer_class = HealthRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    def create(self, request, *args, **kwargs):
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để xác nhận lịch khám này."
        if request.user.role == UserRole.BAC_SI:
            validated_data = {
                "patient_id": request.data['patient_id'],
                "doctor_id": request.user.id,
                "symstoms": request.data['symstons']
            }
            hr = HealthRecord(**validated_data)
            hr.save()
            if request.data['services'] != []:
                for s in request.data['services']:
                    hr.services.add(Service.objects.get(pk=s))
            msg = self.serializer_class(hr, context={'request': request}).data
        return Response(msg, status=status.HTTP_200_OK)
    @action(methods=['post'], detail=True)
    def medicines(self, request, pk=None):
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để xác nhận lịch khám này."
        if request.user.role == UserRole.BAC_SI:
            hr = HealthRecord.objects.get(pk = pk)
            medicines = request.data['medicines']
            for m in medicines:
                if MedicineDetails.objects.filter(health_record=hr, medicine_id=m['id']).first() is None:
                    temp = MedicineDetails(health_record=hr, medicine_id = m['id'], amount = m['amount'], unit= m['unit'])
                    temp.total =temp.amount * list(filter(lambda x: x.unit == temp.unit, temp.medicine.prices.all()))[0].unit_price
                    temp.save()
                    for i in m['instructions']:
                        intr = Instruction.objects.filter(amount__exact=i['amount'], unit__exact=temp.unit, period__exact=i['period']).first()
                        if intr is None:
                            intr = Instruction(**i)
                            intr.unit = temp.unit
                            intr.save()
                        print(intr.id)
                        temp.instructions.add(intr)
                    temp.save()
            msg = self.serializer_class(hr, context={"request": request}).data
        return Response(msg, status=status.HTTP_200_OK)
    @action(methods=['put'], detail=True)
    def lock(self, request, pk=None):
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để khóa toa thuốc này này."
        if request.user.role == UserRole.BAC_SI:
            hr = HealthRecord.objects.get(pk=pk)
            hr.locked = False
            hr.save()
            msg = self.serializer_class(hr, context={"request": request}).data
        return Response(msg, status=status.HTTP_200_OK)
    @action(methods=['put'], detail=True)
    def change_service(self, request, pk=None):
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để xác nhận lịch khám này."

        if request.user.role == UserRole.BAC_SI:
            hr = HealthRecord.objects.get(pk=pk)
            if hr.locked:
                msg['message'] = "Bạn không thể sửa đổi những dịch vụ đã khóa"
            else:
                services = request.data['services']
                s = hr.services.all()
                i = 0
                while i < len(s):
                    if s[i].id in services:
                        services.remove(s[i].id)
                    else:
                        hr.services.remove(s[i])
                        i-=1
                    i+=1
                for s in services:
                    hr.services.add(Service.objects.get(pk=s))
                hr.save()
                msg = success.copy()
        return Response(msg, status=status.HTTP_200_OK)

class PatientViewSet(ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    def get_serializer_class(self):
        if self.action == "list":
            return PatientListSerializer
        else:
            return PatientSerializer

class InstructionViewSet(ViewSet, generics.ListAPIView):
    queryset = Instruction.objects.filter(active=True)
    serializer_class = InstructionSerializer
