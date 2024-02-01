from django.urls import path, include
from . import views, admin
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('medicines', views.MedicineViewSet, basename='medicines')
router.register('doctor', views.DoctorViewSet, basename='doctor')
router.register('user', views.UserViewSet, basename='user')
router.register('appointment', views.AppointmentViewSet)
urlpatterns = [

    path('', include(router.urls)),
    path('admin/', admin.admin_site.urls),
]