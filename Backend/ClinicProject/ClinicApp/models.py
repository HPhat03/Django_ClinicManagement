from django.db import models
from django.contrib.auth.models import AbstractUser
from django_enumfield import enum
# Create your models here.

class UserRole(enum.Enum):
    BAC_SI = "Bác sĩ"
    Y_TA = "Y tá"
    ADMIN = "Admin"
    BENH_NHAN = "Bệnh nhân"
#model
class User(AbstractUser):
    avatar = models.ImageField(upload_to='users/%Y/%m', null=True)
    role = enum.EnumField(UserRole, default=UserRole.BENH_NHAN)




