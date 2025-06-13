from django.urls import path

from vps_rental import views

urlpatterns = [
    path(r"services/", views.ServiceList.as_view(), name="services-list"),
    path(r"services-add/", views.ServiceAdd.as_view(), name="services-add"),
    path(r"services/<int:pk>/", views.ServiceDetail.as_view(), name="services-detail"),
    path(r"app/", views.ApplicationList.as_view(), name="application-list"),
    path(
        r"app/<int:pk>/", views.ApplicationDetail.as_view(), name="application-detail"
    ),
    path(
        r"app/<int:pk>/formed/",
        views.ApplicationFormed.as_view(),
        name="application-formed",
    ),
    path(
        r"app/del/<int:service_id>",
        views.ApplicationDeleteServer.as_view(),
        name="remove-service-from-applic",
    ),
    path(r"register/", views.RegisterView.as_view(), name="register"),
    path(r"login/", views.LoginView.as_view(), name="login"),
    path(r"logout/", views.LogoutView.as_view(), name="logout"),
    path(r"user/", views.UserView.as_view(), name="user"),
]
