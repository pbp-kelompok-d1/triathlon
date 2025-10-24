from django import forms
from .models import Ticket
from place.models import Place

# --- INI PERUBAHANNYA ---
# Definisikan kelas Tailwind untuk input form agar konsisten
tailwind_form_class = "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
# -------------------------

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['customer_name', 'place', 'ticket_quantity', 'booking_date']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': tailwind_form_class, # <-- Diubah
                'placeholder': 'Enter customer name',
                'required': True
            }),
            'place': forms.Select(attrs={
                'class': tailwind_form_class, # <-- Diubah
                'id': 'id_place',
                'required': True
            }),
            'ticket_quantity': forms.NumberInput(attrs={
                'class': tailwind_form_class, # <-- Diubah
                'min': '1',
                'value': '1',
                'id': 'id_ticket_quantity',
                'required': True
            }),
            'booking_date': forms.DateInput(attrs={
                'class': tailwind_form_class, # <-- Diubah
                'type': 'date',
                'required': True
            }),
        }
        labels = {
            'customer_name': 'Customer Name',
            'place': 'Select Sport Place',
            'ticket_quantity': 'Ticket Quantity',
            'booking_date': 'Booking Date',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['place'].queryset = Place.objects.all().order_by('name')
        self.fields['place'].empty_label = "-- Select Place --"
    
    def clean_ticket_quantity(self):
        quantity = self.cleaned_data.get('ticket_quantity')
        if quantity and quantity < 1:
            raise forms.ValidationError("Ticket quantity must be at least 1")
        return quantity