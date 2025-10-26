from django import forms
from .models import Ticket
from place.models import Place
<<<<<<< HEAD

# Definisikan kelas Tailwind untuk input form agar konsisten
tailwind_form_class = "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
=======
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
<<<<<<< HEAD
        fields = ['customer_name', 'place', 'booking_date', 'ticket_quantity']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': tailwind_form_class,
=======
        fields = ['customer_name', 'place', 'ticket_quantity', 'booking_date']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
                'placeholder': 'Enter customer name',
                'required': True
            }),
            'place': forms.Select(attrs={
<<<<<<< HEAD
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
=======
                'class': 'form-control',
                'id': 'id_place',
                'required': True
            }),
            'ticket_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
                'min': '1',
                'value': '1',
                'id': 'id_ticket_quantity',
                'required': True
            }),
<<<<<<< HEAD
        }
        labels = {
            'customer_name': 'Customer Name',
            'place': 'Place Name',
            'booking_date': 'Booking Date',
            'ticket_quantity': 'Ticket Quantity',
=======
            'booking_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }
        labels = {
            'customer_name': 'Customer Name',
            'place': 'Select Sport Place',
            'ticket_quantity': 'Ticket Quantity',
            'booking_date': 'Booking Date',
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
<<<<<<< HEAD
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
=======
        # Hanya tampilkan tempat yang ada dan urutkan berdasarkan nama
        self.fields['place'].queryset = Place.objects.all().order_by('name')
        
        # Tambahkan empty label
        self.fields['place'].empty_label = "-- Select Place --"
    
    def clean_ticket_quantity(self):
        quantity = self.cleaned_data.get('ticket_quantity')
        if quantity and quantity < 1:
            raise forms.ValidationError("Ticket quantity must be at least 1")
        return quantity
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
