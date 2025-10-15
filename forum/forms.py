from django import forms
from .models import ForumPost

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ['title', 'content', 'category', 'sport_category', 'product_id', 'location_id']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title...',
                'maxlength': 255
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your post content...',
                'rows': 8
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'sport_category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'product_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product ID (optional)'
            }),
            'location_id': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter location ID (optional)'
            })
        }
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long.')
        return title
        
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise forms.ValidationError('Content must be at least 10 characters long.')
        return content
    