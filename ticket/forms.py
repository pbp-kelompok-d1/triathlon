from django import forms
from .models import Ticket
from place.models import Place

# Definisikan kelas Tailwind untuk input form agar konsisten
tailwind_form_class = "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['customer_name', 'place', 'booking_date', 'ticket_quantity']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': tailwind_form_class,
                'placeholder': 'Enter customer name',
                'required': True
            }),
            'place': forms.Select(attrs={
                'class': tailwind_form_class,
                'id': 'id_place',
                'required': True
            }),
            'booking_date': forms.DateInput(attrs={
                'class': tailwind_form_class,
                'type': 'date',
                'required': True
            }),
            'ticket_quantity': forms.NumberInput(attrs={
                'class': tailwind_form_class,
                'min': '1',
                'value': '1',
                'id': 'id_ticket_quantity',
                'required': True
            }),
        }
        labels = {
            'customer_name': 'Customer Name',
            'place': 'Place Name',
            'booking_date': 'Booking Date',
            'ticket_quantity': 'Ticket Quantity',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['place'].queryset = Place.objects.all().order_by('name')
        self.fields['place'].empty_label = "-- Select Place --"
        
        # Set default value untuk ticket_quantity jika tidak ada
        if not self.instance.pk and 'ticket_quantity' not in self.data:
            self.fields['ticket_quantity'].initial = 1
    
    def clean_ticket_quantity(self):
        quantity = self.cleaned_data.get('ticket_quantity')
        if quantity is None:
            return 1  # Default value jika kosong
        if quantity < 1:
            raise forms.ValidationError("Ticket quantity must be at least 1")
        return quantity
    
    def clean(self):
        cleaned_data = super().clean()
        # Pastikan ticket_quantity selalu ada
        if 'ticket_quantity' not in cleaned_data or cleaned_data['ticket_quantity'] is None:
            cleaned_data['ticket_quantity'] = 1
        return cleaned_data
