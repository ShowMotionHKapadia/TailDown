
from django.urls import path
from customer.views import customer_dashboard_view, password_change_view, customer_order_view

urlpatterns = [
    path('dashboard', customer_dashboard_view, name='customer_dashboard'),
    path('order', customer_order_view, name='customer_order'),
    path('password-change/', password_change_view, name='password_change'),
]