from django.urls import path
from account.views import home, login_view, register_view, activate_account,  password_reset_view, password_reset_confirm_view
from . import views


urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('profile/', views.view_profile, name='view_profile'),
    path('activate/<str:uidb64>/<str:token>/',
         activate_account, name='activate'),
    path('password_reset/', password_reset_view, name='password_reset'),
    path('password_reset_confirm/<uidb64>/<token>/', password_reset_confirm_view, name='password_reset_confirm'),
    path('logout/', views.logout_view, name='logout'),
]
