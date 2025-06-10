from django.urls import path
from vps_rental import views

urlpatterns = [
    path(r"services/", views.ServiceList.as_view(), name="services-list"),
    path(r"services-add/", views.ServiceAdd.as_view(), name="services-add"),
    path(r"services/<int:pk>/", views.ServiceDetail.as_view(), name="services-detail"),
]
