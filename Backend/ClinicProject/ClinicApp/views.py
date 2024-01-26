
from django.http import HttpResponse, request


# Create your views here.

def test(request):
    return HttpResponse("Hello")