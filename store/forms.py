from .models import Ticket, HealthInformation
from .models import Review
from .models import Address, Profile, Shipping, TicketReply
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=100, required=True)
    mobile = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User  # or CustomUser
        fields = ['name', 'email', 'mobile', 'password1', 'password2']

    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        user.username = self.cleaned_data['email']  # Using email as username
        if commit:
            user.save()
            # Save mobile number to profile
            Profile.objects.create(
                user=user, mobile=self.cleaned_data['mobile'])
        return user


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_type', 'address_1', 'address_2',
                  'country', 'state', 'city', 'postal_code',]


class ShippingForm(forms.ModelForm):
    class Meta:
        model = Shipping
        fields = ['address_type', 'address_1', 'address_2',
                  'country', 'state', 'city', 'postal_code',]


class GuestRegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    mobile = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        first_name = cleaned_data.get("first_name")
        mobile = cleaned_data.get("mobile")

        if not email:
            self.add_error('email', 'Email is required.')
        if not first_name:
            self.add_error('first_name', 'First name is required.')
        if not mobile:
            self.add_error('mobile', 'Mobile number is required.')


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ProductSearchForm(forms.Form):
    query = forms.CharField(
        label='Search',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search products...'})
    )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'deparment', 'description', 'attachments']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            # Department field
            'deparment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            # Attachments field
            'attachments': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['comment']


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter your message...'}),
        }
