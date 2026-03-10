
from django.urls import path
from customer.views import (access_denied,CustomerDashboardView,password_change_view, customer_order_view, customer_order_cart, delete_cart_item)

urlpatterns = [
    path('access-denied/',access_denied, name='access_denied'),
    path('dashboard',CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('order', customer_order_view, name='customer_order'),
    path('cart', customer_order_cart, name='customer_order_cart'),
    path('cart/delete/<uuid:order_id>/', delete_cart_item, name='delete_cart_item'),
    path('password-change/', password_change_view, name='password_change'),
]