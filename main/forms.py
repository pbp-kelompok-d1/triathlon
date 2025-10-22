from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from user_profile.models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm',
            'placeholder': 'email@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm',
            'placeholder': 'Last name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm',
            'placeholder': '+1234567890'
        })
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        initial='USER',
        widget=forms.Select(attrs={
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'phone_number', 'role')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        
        # Add custom classes to username and password fields
        self.fields['username'].widget.attrs.update({
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'block w-full px-3 py-2 mt-1 text-red-800 bg-red-100 border border-red-300 rounded-md shadow-sm focus:outline-none focus:ring-green-500 focus:border-green-500 sm:text-sm',
            'placeholder': 'Confirm password'
        })

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Update the UserProfile that was automatically created by the signal
            profile = user.profile
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.role = self.cleaned_data['role']
            profile.save()
        
        return user
