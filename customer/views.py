from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator 
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin

from account.models import JobDetails
from customer.models import TailDownCart, TailDownOrder
from .forms import TailDownCartForm

@never_cache
def access_denied(request):
    return render(request, 'customer/access_denied.html')

@never_cache
@login_required
@csrf_protect
@permission_required('customer.add_taildowncart', raise_exception=True)
def customer_order(request):
    """
    Handles the tail-down order form.
    - POST: validates and saves the order, attaching it to the logged-in user.
    - GET:  renders a blank order form with all dropdown/radio/checkbox options.
    """
    if request.method == "POST":
        form = TailDownCartForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.save()
            messages.success(request, "Order Added to the Cart successfully!")
            return redirect('customer_order')
        else:
            #Surface each field-level validation error as a flash message
            for field, error_list in form.errors.items():
                for error in error_list:
                    # Use the human-readable field label when available
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
        
    else:
        form = TailDownCartForm() # Blank form for a fresh GET request

    #Fetch all jobs for the Show Name dropdown
    showNames_qs = JobDetails.objects.all()

    #Build the template context manually so the template can render
    #each input generically without hard-coding field types in HTML.
    context = {
        "form": form,

        #Plain text input for the order name
        "orderName":{'type':'text', 'id':'orderNameId', 'name':'orderName'},

        #Numeric input for how many units to order
        "orderQuantity":{'type':'number', 'id':'orderQuantityId', 'name':'quantity'},

        #Show name dropdown — options are built from live JobDetails records
        "showName": {
            'type': 'select', 'id': 'showNameId', 'name': 'showName', 
            'options': [{'key': obj.jobId, 'value': obj.showName} for obj in showNames_qs]
        },

        #Cable finish options (Galvanized / Blackened)
        "cableFinishes": {
            'type': 'select', 'id': 'cableFinishesId', 'name': 'cableFinishes', 
            'options': [{'key': 'GAL', 'value': 'Galvanized'}, {'key': 'BLK', 'value': 'Blackened'}]
        },

        #Standard cable diameter sizes
        "cableSize": {
            'type': 'select', 'id': 'cableSizeId', 'name': 'cableSize', 
            'options': [{'key': '1/4"', 'value': '1/4"'}, {'key': '1/8"', 'value': '1/8"'}, {'key': '1/16"', 'value': '1/16"'}, {'key': '3/8"',  'value': '3/8"'}, {'key': '3/16"', 'value': '3/16"'}, {'key': '5/16"', 'value': '5/16"'},] 
        },

        #Radio buttons for selecting the top fitting type; each carries an illustration
        "top": [
            {'type': 'radio', 'name': 'topType', 'value': 'Big', 'image': "images/Top_2.JPG"}, 
            {'type': 'radio', 'name': 'topType', 'value': 'Small', 'image': "images/Top.JPG"},
            {'type': 'radio', 'name': 'topType', 'value': 'None',  'image': "images/official_special_lowres.gif"}
        ],

        #Radio buttons for selecting the end fitting type
        "end": [
            {'type': 'radio', 'name': 'endType', 'value': 'Nico', 'image': "images/Bottom_1.JPG"}, 
            {'type': 'radio', 'name': 'endType', 'value': 'Crosby', 'image': "images/Bottom_2.JPG"},
            {'type': 'radio', 'name': 'endType', 'value': 'None' ,  'image': "images/official_special_lowres.gif"}
        ],

        #Checkboxes for optional hardware add-ons (turnbuckle and/or chain)
        "chkTC": [
            {'type': 'checkbox', 'name': 'turnbuckle', 'value': 'Turnbuckle', 'image': "images/Turnbuckle.JPG"},
            {'type': 'checkbox', 'name': 'chain', 'value': 'Chain', 'image': "images/Chain.JPG"},
        ],

        #Dropdown controlling the assembly order of the selected hardware
        "orderTC": {
            'type': 'select', 'id': 'orderId', 'name': 'tcOrder', 
            'options': [{'key': 'OT', 'value': 'Only Turnbuckle'}, {'key': 'OC',   'value': 'Only Chain'}, {'key': 'TC',   'value': 'Turnbuckle then Chain'}, {'key': 'CT',   'value': 'Chain then Turnbuckle'}, {'key': 'none', 'value': 'None'}]
        },

        #Turnbuckle size dropdown — only relevant when the turnbuckle checkbox is ticked
        "tbSize": {
            'type': 'select', 'id': 'tbSizeId', 'name': 'turnbuckleSize',
            'options': [{'key': '3/8"X6"', 'value': '3/8" X 6"'}, {'key': '1/2"X6"', 'value': '1/2" X 6"'}, {'key': '1/2"X9"', 'value': '1/2" X 9"'}, {'key': '5/8"X6"', 'value': '5/8" X 6"'}, {'key': '5/8"X9"', 'value': '5/8" X 9"'}] 
        },
    }

    return render(request, 'customer/order.html', context=context)

@never_cache
@login_required
@csrf_protect
@permission_required('customer.add_taildowncart', raise_exception=True)
def customer_order_cart(request):
    if request.method == 'POST':
        userCartItems = TailDownCart.objects.filter(customer=request.user, isOrdered=False)

        if not userCartItems.exists():
            return redirect('customer_order_cart')
        
        try:
            with transaction.atomic():
                for item in userCartItems:
                    # 1. Create the permanent Order record
                    TailDownOrder.objects.create(
                        customer=item.customer,
                        orderName=item.orderName,
                        cableFinishes=item.cableFinishes,
                        cableSize=item.cableSize,
                        showName=item.showName,
                        topType=item.topType,
                        endType=item.endType,
                        turnbuckle=item.turnbuckle,
                        chain=item.chain,
                        tcOrder=item.tcOrder,
                        turnbuckleSize=item.turnbuckleSize,
                        quantity=item.quantity,
                        status="Placed" # Or "Pending"
                    )
                    
                    # 2. Mark the cart item as ordered
                    item.isOrdered = True
                    item.save()

                messages.success(request, f"Thank you, {request.user.first_name}! Your order has been placed successfully. "
                                        "Our team will begin processing it shortly.")
                return redirect('dashboard')

        except Exception as e:
            # Handle errors (e.g., database issues)
            print(f"Error processing order: {e}")

    # GET request logic    
    userCarts = TailDownCart.objects.filter(customer=request.user, isOrdered=False)
    userName = request.user.first_name
    context = {
            'cartDetails':userCarts,
            'userName': userName
            }
    return render(request, 'customer/cart.html', context=context)

decorators = [never_cache, login_required, csrf_protect]
@method_decorator(decorators, name='dispatch')
class DashboardView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = TailDownOrder
    permission_required = 'customer.view_taildownorder'
    template_name = 'customer/dashboard.html'
    context_object_name = 'orders'
    
    def get_queryset(self):
        user = self.request.user
        # User and superusers see every order in the system with permission.
        if user.is_superuser or user.has_perm('customer.view_all_taildownorders'):
            queryset = TailDownOrder.objects.all().order_by('-created_at')
        else:
            queryset = TailDownOrder.objects.filter(
                customer=user
            ).order_by('-created_at')

        show_filter = self.request.GET.get('show')
        if show_filter:
            queryset = queryset.filter(showName__jobId=show_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass all jobs to the sidebar for the dropdown filter
        context['all_jobs'] = JobDetails.objects.all()
        return context

@never_cache
@login_required
@require_POST  # Only POST allowed, blocks accidental GET deletions.
@csrf_protect
@permission_required('customer.delete_taildowncart', raise_exception=True)
def delete_cart_item(request, order_id):
    """
    Securely deletes a cart item via AJAX.
    - Ownership is always verified: users can only delete their own items.
    - Returns message so the frontend can handle it gracefully.
    """
    cart_item = get_object_or_404(TailDownCart, orderId=order_id, customer=request.user)
    cart_item.delete()  
    return JsonResponse({
        'status': 'success',
        'message': 'Item removed from cart.'
    })

@never_cache
@login_required
@csrf_protect
def password_change_view(request):
    """
    Allows a logged-in user to change their password.
    - POST: validates the change form; on success, logs the user out so they
            must re-authenticate with the new password.
    - GET:  renders the blank password change form.
    """
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            logout(request)  #Invalidate the current session after the password change
            messages.success(
                request, "Password changed successfully. Please log in with your new password."
            )
            return redirect('login')
        else:
           #Show each validation error (e.g. wrong old password, mismatched new passwords).
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'customer/password_change.html', {'form': form})
    