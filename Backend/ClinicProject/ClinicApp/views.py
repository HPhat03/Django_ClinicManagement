from django.http import HttpResponse, request
from rest_framework.viewsets import ModelViewSet

from .models import Medicine
from .serializers import MedicinePriceSerializer, MedicineSerializer


# Create your views here.

def test(request):
    return HttpResponse("Hello")


class MedicineViewSet(ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer

