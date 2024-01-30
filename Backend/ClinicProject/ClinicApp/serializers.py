from rest_framework.serializers import ModelSerializer,Serializer
from .models import Medicine, MedicinePrice, Vendor


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
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'vendor', 'content', 'image', 'prices']
