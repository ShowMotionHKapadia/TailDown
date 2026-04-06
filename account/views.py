from django.conf import settings
from django.shortcuts import render, redirect
from account.forms import RegistrationForm, PasswordResetForm, UserProfileForm
from django.contrib import messages

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from account.utils import send_activation_email, send_reset_password_email
from account.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import SetPasswordForm
from django.views.decorators.cache import never_cache 
from django.contrib.auth.decorators import login_required 
from axes.handlers.proxy import AxesProxyHandler

@never_cache
def home(request):
    return render(request, 'account/home.html')

@never_cache
def login_view(request):    
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if AxesProxyHandler.is_locked(request, credentials={'username': email}):
            messages.error(
                request, 
                "Your account has been temporarily locked due to too many "
                "failed login attempts. Please try again later."
            )
            return redirect('login')

        user = authenticate(request, email=email, password=password)

        # try:
        #     user = User.objects.get(email=email)
        # except User.DoesNotExist:
        #     messages.error(request, "Invalid email or password.")
        #     return redirect('login')

        # 2. Check the password manually
        # if not user.check_password(password):
        #     messages.error(request, "Invalid email or password.")
        #     return redirect('login')

        # if not user.is_active:
        #     messages.error(
        #         request, "Your account is inactive. Please activate your account."
        #     )
        #     # uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        #     # token = default_token_generator.make_token(user)
        #     # activation_link = reverse(
        #     #     'activate', kwargs={'uidb64': uidb64, 'token': token})
        #     # activation_url = f'{settings.SITE_DOMAIN}{activation_link}'
        #     # send_activation_email(user.email, activation_url)
        #     return redirect('login')

        if user is not None:
            # ── KEEP: is_active check, but now it's AFTER authentication ──
            if not user.is_active:
                messages.error(
                    request, 
                    "Your account is inactive. Please activate your account."
                )
                return redirect('login')

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(
                request, 
                f"Welcome back, {request.user.first_name.capitalize()}!"
            )
            
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'account/login.html')

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.is_active = False
            user.save()

            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = reverse(
                'activate', kwargs={'uidb64': uidb64, 'token': token})
            activation_url = f'{settings.SITE_DOMAIN}{activation_link}'
            send_activation_email(user.email, activation_url)
            messages.success(
                request,
                'Registration successful! Please check your email to activate your account.',
            )
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'account/register.html', {'form': form})

@never_cache
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if user.is_active:
            messages.warning(
                request, "This account has already been activated.")
            return redirect('login')

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(
                request, "Your account has been activated successfully!"
            )
            return redirect('login')
        else:
            messages.error(
                request, "The activation link is invalid or has expired."
            )
            return redirect('login')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "Invalid activation link.")
        return redirect('login')

@never_cache
def password_reset_view(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            user = User.objects.filter(email=email).first()
            if user:
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = reverse(
                    'password_reset_confirm',
                    kwargs={'uidb64': uidb64, 'token': token},
                )
                absolute_reset_url = f"{request.build_absolute_uri(reset_url)}"
                send_reset_password_email(user.email, absolute_reset_url)
            messages.success(
                request, (
                    "We have sent you a password reset link. Please check your email.")
            )
            return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, 'account/password_reset.html', {'form': form})

@never_cache
def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            messages.error(request, ('This link has expired or is invalid.'))
            return redirect('password_reset')

        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request, ('Your password has been successfully reset.')
                )
                return redirect('login')
            else:
                for errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        else:
            form = SetPasswordForm(user)

        return render(
            request, 'account/password_reset_confirm.html', {
                'form': form, 'uidb64': uidb64, 'token': token}
        )

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, (
            'An error occurred. Please try again later.'))
        return redirect('password_reset')

@never_cache
@login_required
def view_profile(request):
    user = request.user
    if request.method == 'POST':
        # Store the old email to compare later
        old_email = user.email
        old_phone = user.phone
        form = UserProfileForm(request.POST, instance=user)
        
        if form.is_valid():
            new_email = form.cleaned_data.get('email')
            new_phone = form.cleaned_data.get('phone')
            
            if new_phone != old_phone:
                user.phone = new_phone
                form.save(commit=False)  # Save the form but don't commit to DB yet
                user.save()  # Now save the user with the updated phone number
                messages.success(request, "Phone number updated successfully!")
            
            # Save the form first
            updated_user = form.save(commit=False)
            
            # Logic: If email changed, deactivate account
            if new_email != old_email:
                updated_user.is_active = False
                updated_user.email = new_email
                updated_user.save()
                            
                # Send activation email to the new email address
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                activation_link = reverse(
                    'activate', kwargs={'uidb64': uidb64, 'token': token})
                activation_url = f'{settings.SITE_DOMAIN}{activation_link}'
                send_activation_email(new_email, activation_url)
                messages.success(request,'Email updated. Your account has been deactivated for verification. Please check your email to activate your account.')
                return redirect('login')
            
            messages.success(request, "Profile updated successfully!")
            return redirect('view_profile')
    else:
        form = UserProfileForm(instance=user)
    
    return render(request, 'account/view_profile.html', {'form': form})

@never_cache
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect('login')
    return redirect('home') # Safety redirect if someone tries a GET request