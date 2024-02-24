import datetime

from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser,FileUploadParser
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, generics

from .models import Medicine, User, Doctor, UserRole, Appointment, Confirmation, HealthRecord, Service, \
    MedicineDetails, Instruction, Patient, Department, Receipt, ReceiptDetail, Unit, Period
from .serializers import MedicineSerializer, UserSerializer, DoctorSerializer, \
    MedicineListSerializer, DoctorListSerializer, AppointmentSerializer, AppointmentListSerializer, \
    HealthRecordSerializer, PatientListSerializer, PatientSerializer, InstructionSerializer,\
    DepartmentSerializer, NonDetailEmployeeSerializer, ReceiptSerializer, ServiceSerializer, HealthRecordListSerializer
from .pagination import MedicinePagnigation, AppointmentPagnigation

from django.core.mail import send_mail

# MESSAGE
success = {"status": "success", "message": "Thanh cong"}
failed = {"status": "failed", "message": "That Bai"}
# OTHER
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

    @action(methods=['get'], detail=True)
    def unit(self, request, pk=None):
        p = Medicine.objects.get(pk=pk).prices.all()
        units = []
        for i in p:
            temp = {
                    "value": i.unit.name,
                    "key": i.unit.value
                }
            print(temp)
            units.append(temp)
        return Response(units, status=status.HTTP_200_OK)



class DoctorViewSet(ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    def list(self, request, *args, **kwargs):
        return Response(DoctorListSerializer(self.queryset, context={"request": request}, many=True).data,
                        status=status.HTTP_200_OK)


class UserViewSet(ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [MultiPartParser, ]

    def initialize_request(self, request, *args, **kwargs):

        request = super().initialize_request(request, *args, **kwargs)
        print(request.method)
        if request.method in ['POST']:
            request.parsers = [MultiPartParser(), FileUploadParser()]
        else:
            request.parsers = []

        self.action = self.action_map.get(request.method.lower())
        return request

    def create(self, request, *args, **kwargs):
        msg= failed.copy()
        msg['message'] = "Bạn không đủ quyền hạn để thực hiện chức năng này"
        if 'role' in request.data.keys():
            if request.user.is_authenticated and request.user.role == UserRole.ADMIN:
                return super().create(request=self.request, *args, **kwargs)
            else:
                return Response(msg, status=status.HTTP_403_FORBIDDEN)
        else:
            return super().create(request, *args, **kwargs)

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
                obj = PatientSerializer(queryset, fields=[], context={'request': request})
            elif queryset.role == UserRole.BAC_SI:
                queryset = queryset.employee
                obj = NonDetailEmployeeSerializer(queryset, fields=['diploma', 'doctor_info'],
                                                  context={'request': request})
            elif queryset.role == UserRole.Y_TA:
                queryset = queryset.employee.nurse_info
                obj = NonDetailEmployeeSerializer(queryset.employee_info, fields=["diploma", "nurse_info"],
                                                  context={'request': request})
            data['further_info'] = obj.data
            return Response(data, status=status.HTTP_200_OK)
        else:
            msg = failed.copy()
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)


class AppointmentViewSet(ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Appointment.objects.filter(active=True)
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AppointmentPagnigation


    def get_serializer_class(self):
        if self.action == 'list':
            s = AppointmentListSerializer
        else:
            s = AppointmentSerializer
        return s

    def create(self, request, *args, **kwargs):
        msg = failed.copy()
        msg['message'] = f"{request.user.role} không thể đặt lịch khám"
        if request.user.role == UserRole.BENH_NHAN:
            reg_date = datetime.datetime.strptime(request.data['ExpectedDate'], '%d-%m-%Y %H:%M')
            amount = Appointment.objects.filter(ExpectedDate__date=reg_date.date(), active=True).count()
            if reg_date < datetime.datetime.now():
                msg=failed.copy()
                msg['message'] = f"Không thể đặt lịch khám trước thời gian hiện tại."
            elif amount >= Limit_appointment:
                msg = failed.copy()
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

    @action(methods=['get'], detail=False)
    def current_patient_sucess(self, request):
        msg = failed.copy()
        msg['message'] = "Chỉ có bệnh nhân mới xem đc lịch khám của mình này."
        if request.user.role == UserRole.BENH_NHAN:
            queryset = Appointment.objects.filter(patient_id__exact=request.user.id, created_date__lt= datetime.datetime.now(), active=True)
            print(queryset)
            return Response(AppointmentListSerializer(queryset,many=True, context={'request': request}).data, status=status.HTTP_200_OK)
        return Response(msg, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['get'], detail=False)
    def current_patient_canceled(self, request):
        msg = failed.copy()
        msg['message'] = "Chỉ có bệnh nhân mới xem đc lịch khám của mình này."
        if request.user.role == UserRole.BENH_NHAN:
            queryset = Appointment.objects.filter(patient_id__exact=request.user.id, active=False)
            return Response(AppointmentListSerializer(queryset,many=True, context={'request': request}).data,
                            status=status.HTTP_200_OK)
        return Response(msg, status=status.HTTP_403_FORBIDDEN)

    @action(methods=['get'], detail=False)
    def current_patient_recent(self, request):
        msg = failed.copy()
        msg['message'] = "Chỉ có bệnh nhân mới xem đc lịch khám của mình này."
        if request.user.role == UserRole.BENH_NHAN:
            queryset = Appointment.objects.filter(patient_id__exact=request.user.id, created_date__gte=datetime.datetime.now(), active=True)
            return Response(AppointmentListSerializer(queryset,many=True, context={'request': request}).data,
                            status=status.HTTP_200_OK)
        return Response(msg, status=status.HTTP_403_FORBIDDEN)

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
                temp = Confirmation(appointment=apm, nurse_id=request.user.id)
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
                    message=f'''
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
                    recipient_list=[patient.email]
                )
                print(t)
        return Response(msg, status=status.HTTP_200_OK)


class HealthRecordViewSet(ViewSet, generics.ListAPIView, generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = HealthRecord.objects.filter(active=True)
    serializer_class = HealthRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return HealthRecordListSerializer
        else:
            return HealthRecordSerializer

    def create(self, request, *args, **kwargs):
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để xác nhận lịch khám này."
        if request.user.role == UserRole.BAC_SI:
            validated_data = {
                "patient_id": request.data['patient_id'],
                "doctor_id": request.user.id,
                "symstoms": request.data['symstoms'],
                "overview": request.data['overview']
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
            hr = HealthRecord.objects.get(pk=pk)
            medicines = request.data['medicines']
            if request.data['override']:
                MedicineDetails.objects.filter(health_record=hr).delete()
            for m in medicines:
                print(Unit[m['unit']])
                md = MedicineDetails.objects.filter(health_record=hr, medicine_id=m['id']).first()
                if md is None:
                    temp = MedicineDetails(health_record=hr, medicine_id=m['id'], amount=m['amount'], unit=Unit[m['unit']])
                else:
                    temp = md
                    temp.amount = m['amount']
                    temp.unit = Unit[m['unit']]

                price= temp.medicine.prices.filter(unit=temp.unit)
                price_len= temp.medicine.prices.filter(unit=temp.unit).count()
                print(f"{price} - Xuất ra xem ntn - {price_len}")
                if price_len == 0:
                    msg['message'] = f"Hiện {temp.medicine.name} không phân phối theo {temp.unit}"
                    return Response(msg, status=status.HTTP_200_OK)

                temp.total = temp.amount * price[0].unit_price


                temp.save()
                for i in m['instructions']:
                    intr = Instruction.objects.filter(amount__exact=i['amount'], unit=Unit[i['unit']],period__exact=Period[i['period']]).first()
                    if intr is None:
                        intr = Instruction(period=Period[i['period']], amount=i['amount'], unit=Unit[i['unit']])
                        intr.save()
                    add = True
                    for i in temp.instructions.all():
                        if intr == i:
                            add=False
                            break
                        elif intr.period == i.period:
                            temp.instructions.remove(i)
                            break

                    if add:
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

        if request.user.role in [UserRole.BAC_SI, UserRole.Y_TA]:
            hr = HealthRecord.objects.get(pk=pk)
            if hr.locked:
                msg['message'] = "Bạn không thể sửa đổi những dịch vụ đã khóa"
            else:
                services = request.data['services']
                for s in hr.services.all():
                    print(s.id)
                    if s.id in services:
                        services.remove(s.id)
                    else:
                        try:
                            hr.services.remove(s)
                        except Exception:
                            break
                for s in services:
                    print(Service.objects.get(pk=s))
                    hr.services.add(Service.objects.get(pk=s))

                hr.save()
                msg = success.copy()
        return Response(msg, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def make_receipt(self, request, pk=None):
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để xuất hóa đơn toa thuốc này."

        if request.user.role == UserRole.Y_TA:
            hr = HealthRecord.objects.get(pk=pk)
            if hr.locked:
                msg['message'] = "Bạn không thể xuất hóa đơn toa thuốc đã khóa"
            else:
                receipt = Receipt(record=hr, nurse_id=request.user.id, total=0)
                receipt.save()
                print(receipt.record.id)
                if hr.services.all() != []:
                    for s in hr.services.all():
                        temp = ReceiptDetail(receipt=receipt, name=s.name, price=s.price)
                        temp.save()
                        receipt.detail.add(temp)

                medicinesPrice = MedicineDetails.objects.filter(health_record=hr).aggregate(Sum('total'))

                print(medicinesPrice)
                if medicinesPrice != 0:
                    medicineReceipt = ReceiptDetail(receipt=receipt, name="Thuốc", price=medicinesPrice['total__sum'])
                    medicineReceipt.save()

                    receipt.detail.add(medicineReceipt)
                receipt.total = ReceiptDetail.objects.filter(receipt=receipt).aggregate(Sum('price'))['price__sum']
                hr.locked = True

                receipt.save()
                hr.save()

                msg = ReceiptSerializer(receipt, context={"request": request}).data
        return Response(msg, status=status.HTTP_200_OK)
    @action(methods=['get'], detail=True)
    def receipt(self, request, pk=None):
        msg = failed.copy()
        msg['message'] = "Bạn không đủ quyền để xem hóa đơn toa thuốc này."

        if request.user.role in [UserRole.Y_TA, UserRole.BENH_NHAN]:
            hr = HealthRecord.objects.get(pk=pk)
            if hr.receipt:
                receipt = hr.receipt
                msg = ReceiptSerializer(receipt, context={"request": request}).data
            else:
                msg = failed.copy()
                msg['message']='không tìm thấy hóa đơ, vui lòng tạo hóa đơn trước khi xem'
        return Response(msg, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def my_health_record(self, request):
        msg = failed.copy()
        msg['message'] = "Chỉ có bệnh nhân mới có thể xem toa thuốc của mình."

        if request.user.role == UserRole.BENH_NHAN:
            hr = HealthRecord.objects.filter(patient_id=request.user.id)
            msg = HealthRecordListSerializer(hr, context={"request": request}).data
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


class DepartmentViewSet(ViewSet, generics.ListAPIView):
    queryset = Department.objects.filter(active=True)
    serializer_class = DepartmentSerializer
    # pagination_class = MedicinePagnigation

    @action(methods=['get'], detail=True)
    def doctors(self, request, pk=None):
        queryset = Department.objects.get(pk=pk)
        queryset = queryset.doctors
        return Response(DoctorListSerializer(queryset, many=True, context={"request": request}).data,
                        status=status.HTTP_200_OK)

class RecieptViewSet(ViewSet, generics.ListAPIView):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    # permission_classes = permissions.IsAuthenticated

    def get_queryset(self):
        if self.action == "my_receipt":
            print(self.request.user.name)
            return Receipt.objects.filter(record__patient__user_info__id__exact = self.request.user.id)
        return Receipt.objects.all()
    @action(methods=['get'], detail=False)
    def my_receipt(self, request, *args, **kwargs):
        return self.list(self, request, *args, **kwargs)

class ServiceViewSet(ViewSet, generics.ListAPIView):
    queryset = Service.objects.filter(active=True)
    serializer_class = ServiceSerializer
    pagination_class = AppointmentPagnigation