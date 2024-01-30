from django.urls import path, include
from . import views, admin
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('medicines', views.MedicineViewSet)

urlpatterns = [

    path('', include(router.urls)),
    path('admin/', admin.admin_site.urls),
]