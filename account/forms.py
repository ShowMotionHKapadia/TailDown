from django import forms
from account.models import User

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'company_name', 'phone', 'email', 'password', 'confirm_password']

        def clean(self):
            cleaned_data = super().clean()
            password = cleaned_data.get("password")
            confirm_password = cleaned_data.get("confirm_password")

            if password != confirm_password:
                self.add_error('confirm_password', "Password and Confirm Password do not match.")

            return cleaned_data
    
        def clean_email(self):
            email = self.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("User with this email already exists.")
            return email

class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        max_length=255,
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        # Check if a user with this email exists
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                ('No account is associated with this email address.')
            )
        return email
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone','email'] 

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if the email is being changed and if the new email is already taken
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Check if the phone is being changed and if the new phone is already taken
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This phone number is already in use by another account.")
        return phone