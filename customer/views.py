from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .models import TailDownOrder
from account.models import JobDetails
from .forms import TailDownOrderForm

@login_required 
def customer_dashboard_view(request):
    """Renders the customer dashboard landing page."""
    return render(request, 'customer/dashboard.html')

@login_required
def customer_order_view(request):
    """
    Handles the tail-down order form.
    - POST: validates and saves the order, attaching it to the logged-in user.
    - GET:  renders a blank order form with all dropdown/radio/checkbox options.
    """
    if request.method == "POST":
        form = TailDownOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            order.save()
            messages.success(request, "Order placed successfully!")
            return redirect('customer_order')
        else:
            #Surface each field-level validation error as a flash message
            for field, error_list in form.errors.items():
                for error in error_list:
                    # Use the human-readable field label when available
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
        
    else:
        form = TailDownOrderForm() # Blank form for a fresh GET request

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
            {'type': 'radio', 'name': 'topType', 'value': 'Big', 'image': "images/official_special_lowres.gif"}, 
            {'type': 'radio', 'name': 'topType', 'value': 'Small', 'image': "images/official_special_lowres.gif"},
            {'type': 'radio', 'name': 'topType', 'value': 'None',  'image': "images/official_special_lowres.gif"}
        ],

        #Radio buttons for selecting the end fitting type
        "end": [
            {'type': 'radio', 'name': 'endType', 'value': 'Big', 'image': "images/official_special_lowres.gif"}, 
            {'type': 'radio', 'name': 'endType', 'value': 'Small', 'image': "images/official_special_lowres.gif"},
            {'type': 'radio', 'name': 'endType', 'value': 'None' ,  'image': "images/official_special_lowres.gif"}
        ],

        #Checkboxes for optional hardware add-ons (turnbuckle and/or chain)
        "chkTC": [
            {'type': 'checkbox', 'name': 'turnbuckle', 'value': 'Turnbuckle', 'image': "images/official_special_lowres.gif"},
            {'type': 'checkbox', 'name': 'chain', 'value': 'Chain', 'image': "images/official_special_lowres.gif"},
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

@login_required
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
    