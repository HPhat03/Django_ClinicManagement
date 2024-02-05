from rest_framework.pagination import PageNumberPagination


class MedicinePagnigation(PageNumberPagination):
    page_size = 10


