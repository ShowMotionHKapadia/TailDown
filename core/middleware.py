from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

class RestrictCustomerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response    

    def __call__(self, request):
        admin_url = reverse('admin:index')

        if request.path.startswith(admin_url):
            # 2. Check if they are authenticated and are a customer
            if not request.user.is_authenticated or not request.user.is_superuser:
                return redirect('access_denied')  # Redirect to your main landing page
        
        return self.get_response(request)