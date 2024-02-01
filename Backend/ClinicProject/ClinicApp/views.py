import datetime

from django.conf import settings
from django.http import HttpResponse, request
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet, generics

from .models import Medicine, User, Employee, Doctor, UserRole, Appointment, Confirmation
from .serializers import MedicineSerializer, UserSerializer, DoctorSerializer, \
    MedicineListSerializer, DoctorListSerializer, AppointmentSerializer, AppointmentListSerializer
from django.core.mail import send_mail
#MESSAGE
success = {"status": "success", "message": "Thanh cong"}
failed = {"status":"failed", "message": "That Bai"}
#OTHER
Limit_appointment = 2
# Create your views here.

def test(request):
    return HttpResponse("Hello")


class MedicineViewSet(ViewSet, generics.RetrieveAPIView):
    def list(self, request, *args, **kwargs):
        medicines = Medicine.objects.filter(active=True).all()
        return Response(MedicineListSerializer(medicines, many=True, context={'request': request}).data)

    queryset = Medicine.objects.filter(active=True)
    serializer_class = MedicineSerializer

class DoctorViewSet(ViewSet, generics.RetrieveAPIView):
    def list(self, request, *args, **kwargs):
        doctors = Doctor.objects.all()
        return Response(DoctorListSerializer(doctors, many=True, context={'request': request}).data)

    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class UserViewSet(ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, ]

class AppointmentViewSet(ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Appointment.objects.filter(active=True)
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        appointments = Appointment.objects.all()
        return Response(AppointmentListSerializer(appointments, many=True, context={'request': request}).data)
    def create(self, request, *args, **kwargs):
        reg_date =  datetime.datetime.strptime(request.data['ExpectedDate'], '%d-%m-%Y %H:%M')
        print(reg_date.date())
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
                msg = AppointmentSerializer(apm, context={"request": request}).data
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
                msg = AppointmentSerializer(apm, context={"request": request}).data
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


