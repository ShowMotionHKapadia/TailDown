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
    # Everything EXCEPT orderName, quantity, cableLengthFt, cableLengthIn
    RETAIN_FIELDS = [
        'showName', 'deliverBy', 'cableFinishes', 'cableSize',
        'topType', 'endType', 'turnbuckle', 'chain',
        'tcOrder', 'turnbuckleSize', 'chainLength',
    ]

    retained = {}

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

            # Stash the selections we want to survive the redirect
            request.session['taildown_retained'] = {
                k: request.POST.get(k) for k in RETAIN_FIELDS
                if request.POST.get(k) not in (None, '')
            }
            return redirect('customer_order')
        else:
            # Form was invalid — keep ALL user input, including the per-item fields
            retained = {k: request.POST.get(k, '') for k in RETAIN_FIELDS}
            for field, error_list in form.errors.items():
                for error in error_list:
                    field_label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_label}: {error}")
    else:
        # Successful-POST redirect landed here — pull stashed values once
        retained = request.session.pop('taildown_retained', {}) or {}
        form = TailDownCartForm(initial=retained) if retained else TailDownCartForm()

    showNames_qs = JobDetails.objects.all()

    context = {
        "form": form,

        "orderName":     {'type':'text',   'id':'orderNameId',     'name':'orderName'},
        "cableLengthFt": {'type':'number', 'id':'cableLengthFtId', 'name':'cableLengthFt'},
        "cableLengthIn": {'type':'number', 'id':'cableLengthInId', 'name':'cableLengthIn'},
        "orderQuantity": {'type':'number', 'id':'orderQuantityId', 'name':'quantity'},

        "deliverBy": {
            'type':'Date', 'id':'deliverById', 'name':'deliverBy',
            'defaultValue': retained.get('deliverBy') or calDeliveryDate(),
            'minDate': date.today().strftime('%Y-%m-%d'),
        },

        "showName": {
            'type': 'select', 'id': 'showNameId', 'name': 'showName',
            'selected': retained.get('showName'),
            'options': [{'key': obj.jobId, 'value': obj.showName} for obj in showNames_qs],
        },
        "cableFinishes": {
            'type': 'select', 'id': 'cableFinishesId', 'name': 'cableFinishes',
            'selected': retained.get('cableFinishes'),
            'options': [{'key': 'GAL', 'value': 'Galvanized'}, {'key': 'BLK', 'value': 'Blackened'}],
        },
        "cableSize": {
            'type': 'select', 'id': 'cableSizeId', 'name': 'cableSize',
            'selected': retained.get('cableSize'),
            'options': [{'key': '1/4"', 'value': '1/4"'}, {'key': '1/8"', 'value': '1/8"'},
                        {'key': '1/16"', 'value': '1/16"'}, {'key': '3/8"', 'value': '3/8"'},
                        {'key': '3/16"', 'value': '3/16"'}, {'key': '5/16"', 'value': '5/16"'}],
        },

        "top": [
            {'type':'radio','name':'topType','value':'Soft Eye','image':"images/softEye.JPG",
             'checked': retained.get('topType') == 'Soft Eye'},
            {'type':'radio','name':'topType','value':'Hard Eye','image':"images/hardeye.JPG",
             'checked': retained.get('topType') == 'Hard Eye'},
            {'type':'radio','name':'topType','value':'None','image':"images/official_special_lowres.gif",
             'checked': retained.get('topType') == 'None'},
        ],
        "end": [
            {'type':'radio','name':'endType','value':'Nico','image':"images/nico.JPG",
             'checked': retained.get('endType') == 'Nico'},
            {'type':'radio','name':'endType','value':'Crosby','image':"images/crosby.JPG",
             'checked': retained.get('endType') == 'Crosby'},
            {'type':'radio','name':'endType','value':'None','image':"images/official_special_lowres.gif",
             'checked': retained.get('endType') == 'None'},
        ],

        "chkTC": [
            {'type':'checkbox','name':'turnbuckle','value':'Turnbuckle','image':"images/Turnbuckle.svg",
             'checked': bool(retained.get('turnbuckle'))},
            {'type':'checkbox','name':'chain','value':'Chain','image':"images/Chain.svg",
             'checked': bool(retained.get('chain'))},
        ],

        "orderTC": {
            'type': 'select', 'id': 'orderId', 'name': 'tcOrder',
            'selected': retained.get('tcOrder'),
            'options': [{'key':'OT','value':'Only Turnbuckle'},{'key':'OC','value':'Only Chain'},
                        {'key':'TC','value':'Turnbuckle then Chain'},{'key':'CT','value':'Chain then Turnbuckle'},
                        {'key':'none','value':'None'}],
        },
        "tbSize": {
            'type': 'select', 'id': 'tbSizeId', 'name': 'turnbuckleSize',
            'selected': retained.get('turnbuckleSize'),
            'options': [{'key':'3/8"X6"','value':'3/8" X 6"'},{'key':'1/2"X6"','value':'1/2" X 6"'},
                        {'key':'1/2"X9"','value':'1/2" X 9"'},{'key':'5/8"X6"','value':'5/8" X 6"'},
                        {'key':'5/8"X9"','value':'5/8" X 9"'}],
        },
        "chainLength": {
            'type': 'select', 'id': 'chainLengthId', 'name': 'chainLength',
            'selected': retained.get('chainLength'),
            'options': [{'key':'2ft','value':'2 ft'},{'key':'3ft','value':'3 ft'},{'key':'4ft','value':'4 ft'}],
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

    # elements.append(Paragraph("<u>ASSEMBLY INSTRUCTIONS</u>", assembly_title_style))
    elements.append(Paragraph("<u>ASSEMBLY INSTRUCTIONS</u>", assembly_title_style))

    # --- Helper to load an image ---
    def get_assembly_image(filename, img_w=1.4*inch, img_h=1.4*inch):
        clean_filename = filename.replace('.svg', '.JPG')
        path = os.path.join(settings.BASE_DIR, 'static', clean_filename)
        if os.path.exists(path):
            with PILImage.open(path) as pil_img:
                w, h = pil_img.size
                if w > h:
                    pil_img = pil_img.rotate(90, expand=True)
                    pil_img.save(path)
            from reportlab.platypus import Image as RLImage
            return RLImage(path, width=img_w, height=img_h, kind='proportional')
        return Paragraph("No Image", styles['Normal'])

    # --- Length indicator drawing ---
    def create_length_indicator(length_text, draw_height):
        from reportlab.graphics.shapes import Drawing, Line, Polygon, String

        w = 100
        d = Drawing(w, draw_height)

        mid_x = 70
        cap_left = 55
        cap_right = 85

        top_y = draw_height - 8
        bot_y = 8

        # Top horizontal cap
        d.add(Line(cap_left, top_y, cap_right, top_y,
                   strokeWidth=1, strokeColor=colors.black))
        # Bottom horizontal cap
        d.add(Line(cap_left, bot_y, cap_right, bot_y,
                   strokeWidth=1, strokeColor=colors.black))
        # Vertical line (between arrowheads)
        d.add(Line(mid_x, top_y - 8, mid_x, bot_y + 8,
                   strokeWidth=1, strokeColor=colors.black))
        # Top arrowhead — pointing up
        d.add(Polygon(
            points=[mid_x, top_y,
                    mid_x - 3, top_y - 8,
                    mid_x + 3, top_y - 8],
            fillColor=colors.black, strokeColor=colors.black))
        # Bottom arrowhead — pointing down
        d.add(Polygon(
            points=[mid_x, bot_y,
                    mid_x - 3, bot_y + 8,
                    mid_x + 3, bot_y + 8],
            fillColor=colors.black, strokeColor=colors.black))
        # Length text — centered vertically
        d.add(String(mid_x - 10, draw_height / 2 - 5, length_text,
                     fontSize=16, fontName='Helvetica-Bold', textAnchor='end'))

        return d
    
    # --- Collect parts ---
    top_img = None
    top_label = ""
    end_img = None
    end_label = ""
    hw_parts = []

    if order.topType == 'Soft Eye':
        top_img = get_assembly_image('images/softEye.JPG')
        top_label = "1 - TOP: Soft Eye"
    elif order.topType == 'Hard Eye':
        top_img = get_assembly_image('images/hardeye.JPG')
        top_label = "1 - TOP: Hard Eye"

    if order.endType == 'Nico':
        end_img = get_assembly_image('images/nico.JPG')
        end_label = "2 - END: Nico"
    elif order.endType == 'Crosby':
        end_img = get_assembly_image('images/crosby.JPG')
        end_label = "2 - END: Crosby"

    step = 3
    tc_val = order.tcOrder

    if tc_val == 'OT' and order.turnbuckle:
        hw_parts.append((get_assembly_image('images/Turnbuckle_Vertical.JPG'),
                         f"{step} - Turnbuckle ({order.turnbuckleSize})"))
    elif tc_val == 'OC' and order.chain:
        hw_parts.append((get_assembly_image('images/Chain.JPG'),
                         f"{step} - Chain ({order.chainLength})"))
    elif tc_val == 'TC':
        if order.turnbuckle:
            hw_parts.append((get_assembly_image('images/Turnbuckle_Vertical.JPG'),
                             f"{step} - Turnbuckle ({order.turnbuckleSize})"))
            step += 1
        if order.chain:
            hw_parts.append((get_assembly_image('images/Chain.JPG'),
                             f"{step} - Chain ({order.chainLength})"))
    elif tc_val == 'CT':
        if order.chain:
            hw_parts.append((get_assembly_image('images/Chain.JPG'),
                             f"{step} - Chain ({order.chainLength})"))
            step += 1
        if order.turnbuckle:
            hw_parts.append((get_assembly_image('images/Turnbuckle_Vertical.JPG'),
                             f"{step} - Turnbuckle ({order.turnbuckleSize})"))

    # --- Build assembly table ---
    row_h = 1.5 * inch
    length_text = f"{order.cableLengthFt}'{order.cableLengthIn}\""
    indicator = create_length_indicator(length_text, row_h * 2)

    label_style_asm = ParagraphStyle('AsmLabel', fontSize=11, fontName='Helvetica', leading=14)

    assembly_data = []

    # Row 0: indicator (spans 2 rows) + top image + top label
    assembly_data.append([
        indicator,
        top_img or '',
        Paragraph(top_label, label_style_asm)
    ])

    # Row 1: (spanned by indicator) + end image + end label
    assembly_data.append([
        '',
        end_img or '',
        Paragraph(end_label, label_style_asm)
    ])

    # Hardware rows: empty col 1 + image + label
    for hw_img, hw_label in hw_parts:
        assembly_data.append([
            '',
            hw_img,
            Paragraph(hw_label, label_style_asm)
        ])

    asm_table = Table(
        assembly_data,
        colWidths=[1.3 * inch, 1.6 * inch, 3 * inch],
        rowHeights=[row_h] * len(assembly_data)
    )

    asm_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 1)),          # indicator spans Top + End rows
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(asm_table)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Taildown_{order.orderName}.pdf"'
    return response
