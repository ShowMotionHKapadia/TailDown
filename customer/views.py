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
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import View
from datetime import date, timedelta
from django.urls import reverse
import holidays

from account.models import JobDetails
from customer.models import TailDownCart, TailDownOrder
from .forms import TailDownCartForm, TailDownOrderEditForm

import os
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from PIL import Image as PILImage

#Access denied page for unauthorise user
@never_cache
def access_denied(request):
    return render(request, 'customer/access_denied.html')

#Calcuate delivery date for orders
def calDeliveryDate():
    deliveryDate = date.today()
    usHolidays = holidays.US()
    businessDaysAdded = 0

    # Loop until we have successfully counted 14 business days
    while businessDaysAdded < 14:
        deliveryDate += timedelta(days=1)
        
        # Check if the day is a weekend (5=Sat, 6=Sun) OR a holiday
        if deliveryDate.weekday() < 5 and deliveryDate not in usHolidays:
            businessDaysAdded += 1

    # Return in YYYY-MM-DD format for your HTML date input
    return deliveryDate.strftime('%Y-%m-%d')

#Post: Add customer order to cart
#Get: Provide empty page for order
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

            warning = getattr(form, 'cable_length_warning', None)
            if warning:
                messages.warning(request, warning)

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

        # Datepicker for tail down delivery 
        "deliverBy":{'type':'Date', 'id':'deliverById', 'name':'deliverBy', 'defaultValue':calDeliveryDate(), 'minDate': date.today().strftime('%Y-%m-%d') },

        # Cable length 
        "cableLengthFt": {'type': 'number', 'id': 'cableLengthFtId', 'name': 'cableLengthFt'},
        "cableLengthIn": {'type': 'number', 'id': 'cableLengthInId', 'name': 'cableLengthIn'},

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
            {'type': 'radio', 'name': 'topType', 'value': 'Soft Eye', 'image': "images/softEye.JPG"}, 
            {'type': 'radio', 'name': 'topType', 'value': 'Hard Eye', 'image': "images/hardeye.JPG"},
            {'type': 'radio', 'name': 'topType', 'value': 'None',  'image': "images/official_special_lowres.gif"}
        ],

        #Radio buttons for selecting the end fitting type
        "end": [
            {'type': 'radio', 'name': 'endType', 'value': 'Nico', 'image': "images/nico.JPG"}, 
            {'type': 'radio', 'name': 'endType', 'value': 'Crosby', 'image': "images/crosby.JPG"},
            {'type': 'radio', 'name': 'endType', 'value': 'None' ,  'image': "images/official_special_lowres.gif"}
        ],

        #Checkboxes for optional hardware add-ons (turnbuckle and/or chain)
        "chkTC": [
            {'type': 'checkbox', 'name': 'turnbuckle', 'value': 'Turnbuckle', 'image': "images/Turnbuckle.svg"},
            {'type': 'checkbox', 'name': 'chain', 'value': 'Chain', 'image': "images/Chain.svg"},
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

        "chainLength":{
            'type': 'select', 'id': 'chainLengthId', 'name': 'chainLength',
            'options':[{'key': '2ft', 'value': '2 ft'},{'key': '3ft', 'value': '3 ft'},{'key': '4ft', 'value': '4 ft'}]
        },
    }

    return render(request, 'customer/order.html', context=context)

#Post: Store conform order into database 
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
                        deliverBy=item.deliverBy,
                        cableFinishes=item.cableFinishes,
                        cableSize=item.cableSize,
                        cableLengthFt=item.cableLengthFt,
                        cableLengthIn=item.cableLengthIn,
                        showName=item.showName,
                        topType=item.topType,
                        endType=item.endType,
                        turnbuckle=item.turnbuckle,
                        chain=item.chain,
                        tcOrder=item.tcOrder,
                        turnbuckleSize=item.turnbuckleSize,
                        chainLength=item.chainLength,
                        quantity=item.quantity,
                        status="Ordered"
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

#Load customer data
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
        context['min_date'] = date.today().strftime('%Y-%m-%d')
        user = self.request.user
        context['can_change'] = user.has_perm('customer.change_taildownorder')
        context['can_delete'] = user.has_perm('customer.delete_taildownorder')

        return context
    
#return order details  
@never_cache
@login_required
@permission_required('customer.view_taildownorder', raise_exception=True)
def order_detail_data(request, order_uuid):
    user = request.user
    if user.is_superuser or user.has_perm('customer.view_all_taildownorders'):
        order = get_object_or_404(TailDownOrder, orderId=order_uuid)
    else:
        order = get_object_or_404(TailDownOrder, orderId=order_uuid, customer=user)
    data = {
        'orderName': order.orderName,
        'deliverBy': order.deliverBy.strftime('%m/%d/%Y') if order.deliverBy else '',
        'quantity': order.quantity,
        'cableSize': order.cableSize,
        'cableFinishes': order.cableFinishes,
        'cableLengthFt': order.cableLengthFt,
        'cableLengthIn': order.cableLengthIn,
        'topType': order.topType,
        'endType': order.endType,
        'tcOrder': order.tcOrder,
        'turnbuckleSize': order.turnbuckleSize,
        'chainLength': order.chainLength,
    }
    return JsonResponse(data)

#Edit for ordered data save and validate
@method_decorator(decorators, name='dispatch')
class OrderEditView(PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = TailDownOrder
    form_class = TailDownOrderEditForm
    permission_required = 'customer.change_taildownorder'
    slug_field = 'orderId'
    slug_url_kwarg = 'order_uuid'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.has_perm('customer.view_all_taildownorders'):
            return TailDownOrder.objects.all()
        return TailDownOrder.objects.filter(customer=user)

    def form_valid(self, form):
        messages.success(self.request, f'Order "{form.instance.orderName}" updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Collect all errors and show them as flash messages
        # then redirect back to dashboard instead of rendering a template
        for field, error_list in form.errors.items():
            for error in error_list:
                field_label = form.fields[field].label if field in form.fields else field
                messages.error(self.request, f'{field_label}: {error}')
        return redirect('dashboard')

#Get ordered data
@never_cache
@login_required
@permission_required('customer.change_taildownorder', raise_exception=True)
def order_edit_data(request, order_uuid):
    user = request.user
    if user.is_superuser or user.has_perm('customer.view_all_taildownorders'):
        order = get_object_or_404(TailDownOrder, orderId=order_uuid)
    else:
        order = get_object_or_404(TailDownOrder, orderId=order_uuid, customer=user)
        
    data = {
        'orderName': order.orderName,
        'deliverBy': order.deliverBy.strftime('%Y-%m-%d') if order.deliverBy else '',
        'quantity': order.quantity,
        'showName': str(order.showName.jobId),
        'cableSize': order.cableSize,
        'cableFinishes': order.cableFinishes,
        'cableLengthFt': order.cableLengthFt,
        'cableLengthIn': order.cableLengthIn,
        'topType': order.topType,
        'endType': order.endType,
        'turnbuckle': order.turnbuckle,
        'chain': order.chain,
        'tcOrder': order.tcOrder,
        'turnbuckleSize': order.turnbuckleSize,
        'chainLength': order.chainLength,
        'status': order.status,
    }
    return JsonResponse(data)

#Filter order data by date and show name
@never_cache
@login_required
@csrf_protect
@permission_required('customer.view_taildownorder', raise_exception=True)
def filterOrders(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    user = request.user
    if user.is_superuser or user.has_perm('customer.view_all_taildownorders'):
        queryset = TailDownOrder.objects.all().order_by('-created_at')
    else:
        queryset = TailDownOrder.objects.filter(customer=user).order_by('-created_at')

    import json
    body = json.loads(request.body)
    show = body.get('show', '')
    deliver_by = body.get('deliverBy', '')

    if show:
        queryset = queryset.filter(showName__jobId=show)
    if deliver_by:
        queryset = queryset.filter(deliverBy=deliver_by)

    can_change = user.has_perm('customer.change_taildownorder')
    can_delete = user.has_perm('customer.delete_taildownorder')

    orders = []
    for order in queryset:
        orders.append({
            'orderId': str(order.orderId),
            'orderIdShort': str(order.orderId)[:8],
            'orderName': order.orderName,
            'customerName': f"{order.customer.first_name} {order.customer.last_name}",
            'showName': order.showName.showName if order.showName else '',
            'orderedDate': order.created_at.strftime('%m/%d/%Y') if order.created_at else 'N/A',
            'deliverBy': order.deliverBy.strftime('%m/%d/%Y') if order.deliverBy else 'N/A',
            'quantity': order.quantity,
            'status': order.status,
            'printUrl': reverse('print_order', args=[order.orderId])
        })

    return JsonResponse({
        'status': 'success',
        'orders': orders,
        'count': len(orders),
        'can_change': can_change,
        'can_delete': can_delete,
    })

#Delete order data
@method_decorator(decorators, name='dispatch')
class OrderDeleteView(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = 'customer.delete_taildownorder'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.has_perm('customer.view_all_taildownorders'):
            return TailDownOrder.objects.all()
        return TailDownOrder.objects.filter(customer=user)

    def post(self, request, order_uuid):
        try:
            order = self.get_queryset().get(orderId=order_uuid)
            order_name = order.orderName
            order.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'Order "{order_name}" has been deleted.'
            })
        except TailDownOrder.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Order not found.'
            }, status=404)

#Delete cart item from cart page
@never_cache
@login_required
@require_POST 
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

#Password change view for customers
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

#Print order details in PDF format
@never_cache
@login_required
@permission_required('customer.view_taildownorder', raise_exception=True)
def print_taildown_order(request, order_uuid):
    user = request.user
    if user.is_superuser or user.has_perm('customer.view_all_taildownorders'):
        order = get_object_or_404(TailDownOrder, orderId=order_uuid)
    else:
        order = get_object_or_404(TailDownOrder, orderId=order_uuid, customer=user)

    buffer = BytesIO()
    # Margins kept at 20 to maximize vertical space for larger images
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=30, bottomMargin=30, leftMargin=20, rightMargin=20, title=f"{order.orderName}")
    elements = []
    styles = getSampleStyleSheet()

    # --- Styles ---
    company_style = ParagraphStyle('Company', fontSize=22, fontName='Helvetica-Bold')
    show_title_style = ParagraphStyle('ShowTitle', fontSize=12, fontName='Helvetica-Bold', spaceAfter=2)
    label_style = ParagraphStyle('Label', fontSize=9, textColor=colors.grey, textTransform='uppercase', alignment=1)
    value_style = ParagraphStyle('Value', fontSize=13, fontName='Helvetica-Bold', alignment=1)
    assembly_title_style = ParagraphStyle('AssemblyTitle', fontSize=12, fontName='Helvetica', spaceBefore=8, spaceAfter=8)

    # --- Header Section ---
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')

    if os.path.exists(logo_path): 
        logo_img = Image(logo_path, width=2.1*inch, height=0.6*inch, kind='proportional')
    else:
        logo_img = Paragraph("ShowMotion, Inc.", company_style)
    
    show_name = order.showName.showName if order.showName else 'N/A'
    delivery_date = order.deliverBy.strftime('%m/%d/%Y') if order.deliverBy else 'N/A'

    header_data = [[logo_img,
        Paragraph(f"<b>Show:</b> {show_name}<br/><b>Name:</b> {order.orderName}", show_title_style),
        Paragraph(f"<b>Estimated Date:</b><br/>{delivery_date}", show_title_style)
]]

    #Shrink the first column width to 1.5" to force the next column to start sooner
    #Increase the middle column to give the text room to move left
    header_table = Table(header_data, colWidths=[1.5*inch, 3.2*inch, 1.8*inch])

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        #Increase negative padding to -25 to pull the text significantly left
        ('LEFTPADDING', (1,0), (1,0), -25), 
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ])) 

    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.black, spaceBefore=5, spaceAfter=10, hAlign='LEFT'))
    finish_map = {
        "GAL": "Galvanized",
        "BLK": "Blackened"
    }

    # --- Specs Table ---
    specs = [
        [Paragraph("<u>CABLE SIZE</u>", label_style), Paragraph("<u>FINISH</u>", label_style), Paragraph("<u>LENGTH</u>", label_style)],
        [Paragraph(str(order.cableSize or ""), value_style), 
        Paragraph(str(finish_map.get(order.cableFinishes)) or "", value_style), 
        Paragraph(f"{order.cableLengthFt}' {order.cableLengthIn}\"", value_style)],
        [Spacer(1, 8)] * 3,
        [Paragraph("<u>TOP FITTING</u>", label_style), Paragraph("<u>END FITTING</u>", label_style), Paragraph("<u>QUANTITY</u>", label_style)],
        [Paragraph(str(order.topType or ""), value_style), 
        Paragraph(str(order.endType or ""), value_style), 
        Paragraph(str(order.quantity or ""), value_style)]
    ]

    t = Table(specs, colWidths=[2*inch, 2*inch, 2*inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,1), (0,1), 1, colors.black), ('BOX', (1,1), (1,1), 1, colors.black), ('BOX', (2,1), (2,1), 1, colors.black),
        ('BOX', (0,4), (0,4), 1, colors.black), ('BOX', (1,4), (1,4), 1, colors.black), ('BOX', (2,4), (2,4), 1, colors.black), 
        ('TOPPADDING', (0,1), (-1,1), 6), ('BOTTOMPADDING', (0,1), (-1,1), 6),
        ('TOPPADDING', (0,4), (-1,4), 6), ('BOTTOMPADDING', (0,4), (-1,4), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<u>ASSEMBLY INSTRUCTIONS</u>", assembly_title_style))

    def add_assembly_item(filename, label):
        clean_filename = filename.replace('.svg', '.JPG') 
        path = os.path.join(settings.BASE_DIR, 'static', clean_filename)
        
        if os.path.exists(path):
            
            with PILImage.open(path) as pil_img:
                width, height = pil_img.size
               
                if width > height:
                    pil_img = pil_img.rotate(90, expand=True)
                    pil_img.save(path) 
            from reportlab.platypus import Image as RLImage
            img = RLImage(path, width=1.4*inch, height=1.4*inch, kind='proportional')
            elements.append(img)
            elements.append(Paragraph(label, styles['Normal']))
            elements.append(Spacer(1, 6))
    
    # 1. TOP (Always 1st)
    if order.topType == 'Soft Eye': add_assembly_item('images/softEye.JPG', "1 - TOP: Soft Eye")
    elif order.topType == 'Hard Eye': add_assembly_item('images/hardeye.JPG', "1 - TOP: Hard Eye")
    # 2. END (Always 2nd)
    if order.endType == 'Nico': add_assembly_item('images/nico.JPG', "2 - END: Nico")
    elif order.endType == 'Crosby': add_assembly_item('images/crosby.JPG', "2 - END: Crosby")
    # 3 & 4. Hardware Logic (Removed rotation)
    tc_val = order.tcOrder
    
    if tc_val == 'OT':
        if order.turnbuckle:
            add_assembly_item('images/Turnbuckle_Vertical.JPG', f"3 - Turnbuckle ({order.turnbuckleSize})")
            
    elif tc_val == 'OC':
        if order.chain:
            add_assembly_item('images/Chain.JPG', f"3 - Chain ({order.chainLength})")
            
    elif tc_val == 'TC':
        if order.turnbuckle:
            add_assembly_item('images/Turnbuckle_Vertical.JPG', f"3 - Turnbuckle ({order.turnbuckleSize})")
        if order.chain:
            add_assembly_item('images/Chain.JPG', f"4 - Chain ({order.chainLength})")
            
    elif tc_val == 'CT':
        if order.chain:
            add_assembly_item('images/Chain.JPG', f"3 - Chain ({order.chainLength})")
        if order.turnbuckle:
            add_assembly_item('images/Turnbuckle_Vertical.JPG', f"4 - Turnbuckle ({order.turnbuckleSize})")
    # --- Build ---
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Taildown_{order.orderName}.pdf"'
    return response
