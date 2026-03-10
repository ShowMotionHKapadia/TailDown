from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

def is_superuser_Access(user):
    return user.is_authenticated and user.is_superuser

def is_staff_Access(user):
    # Staff cannot be superusers or customers in your logic
    return user.is_authenticated and user.is_staff and not user.is_superuser

def is_customer_Access(user):
    # Assuming customers are regular users who are not staff/superuser
    return user.is_authenticated and not user.is_staff and not user.is_superuser