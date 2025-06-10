from django.urls import path
from vps_rental import views

urlpatterns = [
    path("hello/", views.hello, name="hello"),
]
