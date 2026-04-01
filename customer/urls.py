from django.urls import path
from customer.views import (access_denied,DashboardView,password_change_view, customer_order, customer_order_cart, delete_cart_item, OrderEditView, order_edit_data,OrderDeleteView,order_detail_data,filterOrders)

urlpatterns = [
    path('access-denied/',access_denied, name='access_denied'),
    path('dashboard',DashboardView.as_view(), name='dashboard'),
    path('order', customer_order, name='customer_order'),
    path('cart', customer_order_cart, name='customer_order_cart'),
    path('cart/delete/<uuid:order_id>/', delete_cart_item, name='delete_cart_item'),
    path('order/<uuid:order_uuid>/detail/', order_detail_data, name='order_detail_data'),
    path('order/<uuid:order_uuid>/edit/', OrderEditView.as_view(), name='order_edit'),     
    path('order/<uuid:order_uuid>/data/', order_edit_data, name='order_edit_data'),
    path('order/<uuid:order_uuid>/delete/', OrderDeleteView.as_view(), name='order_delete'),
    path('orders/filter/', filterOrders, name='filter_orders'),
    path('password-change/', password_change_view, name='password_change'),
]