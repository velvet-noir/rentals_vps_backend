from django.urls import path
from . import views


urlpatterns = [
    path(r"services/", views.ServiceList.as_view(), name="services-list"),
    path(r"services/<int:pk>/", views.ServiceDetail.as_view(), name="services-detail"),
    path(r"spec/", views.ServiceSpecList.as_view(), name="services-spec-list"),
    path(
        r"spec/<int:pk>/",
        views.ServiceSpecDetail.as_view(),
        name="services-spec-detail",
    ),
    path(r"applic/", views.ApplicationList.as_view(), name="application-list"),
    path(
        r"applic/<int:pk>/",
        views.ApplicationDetail.as_view(),
        name="application-detail",
    ),
    path(
        r"applic/<int:applic_id>/service/<int:service_id>",
        views.RemoveServiceFromApplicationView.as_view(),
        name="remove-service-from-applic",
    ),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
]
