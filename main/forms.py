from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from user_profile.models import UserProfile


class CustomUserCreationForm(UserCreationForm):
    # Order: username (from Meta), role, email, phone_number, password1, password2
    
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        initial='USER',
        widget=forms.Select(attrs={
            'class': 'block w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'id': 'id_role'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'id': 'id_email',
            'placeholder': 'Enter your email'
        })
    )
    
    phone_number = forms.IntegerField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'id': 'id_phone_number',
            'placeholder': 'Enter your phone number'
        })
    )
    is_facility_admin = forms.BooleanField(
        required=False,
        label='Register as Facility Administrator',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'role', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        
        # Add custom classes to username and password fields
        self.fields['username'].widget.attrs.update({
            'class': 'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'id': 'id_username',
            'placeholder': 'Choose a username',
            'required': True
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'id': 'id_password1',
            'placeholder': 'Enter your password',
            'required': True
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'block w-full px-4 py-3 text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'id': 'id_password2',
            'placeholder': 'Confirm your password',
            'required': True
        })

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Update the UserProfile that was automatically created by the signal
            profile = user.profile
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.role = self.cleaned_data['role']
            profile.save()
        
        return user
