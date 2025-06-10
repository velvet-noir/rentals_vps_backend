from django.urls import path
from vps_rental import views

urlpatterns = [
    path('', views.GetOrders),
    path('order/<int:id>/', views.GetOrder, name='order_url'),

]
