from django.urls import path
from . import views

urlpatterns = [
    path(r"services/", views.ServiceList.as_view(), name="services-list"),
]
