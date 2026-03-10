from .models import TailDownCart

def order_count(request):
    if request.user.is_authenticated:
        count = TailDownCart.objects.filter(customer=request.user, isOrdered=False).count()
        return {'order_count': count}
    return {'order_count': 0}