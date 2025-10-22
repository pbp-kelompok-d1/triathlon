from django import forms
from .models import Place
from .models import Review

from .models import Place, Review 
tailwind_input_class = "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ["name", "city", "province", "genre", "description", "price", "image"]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': tailwind_input_class,
                'placeholder': 'Contoh: Stadion Gelora Bung Karno'
            }),
            'city': forms.TextInput(attrs={
                'class': tailwind_input_class,
                'placeholder': 'Contoh: Jakarta'
            }),
            'province': forms.TextInput(attrs={
                'class': tailwind_input_class,
                'placeholder': 'Contoh: DKI Jakarta'
            }),
            'genre': forms.Select(attrs={  
                'class': tailwind_input_class
            }),
            'description': forms.Textarea(attrs={
                'class': tailwind_input_class,
                'rows': 4,
                'placeholder': 'Jelaskan tentang tempat ini...'
            }),
            'price': forms.NumberInput(attrs={
                'class': tailwind_input_class,
                'placeholder': 'Contoh: 50000'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

        
