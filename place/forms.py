from django import forms
from .models import Place
from .models import Review

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ["name", "city", "province", "description", "image"]

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

        
