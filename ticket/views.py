from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import date
from .models import Ticket
from .forms import TicketForm
from place.models import Place

def ticket_list(request):
    # Gunakan select_related untuk optimasi query
    tickets = Ticket.objects.select_related('place', 'user').all()
    
    # Optional: Filter berdasarkan user jika Anda ingin user hanya melihat tiket mereka
    # if request.user.is_authenticated:
    #     tickets = tickets.filter(user=request.user)
    
    # Filter berdasarkan status (past, today, upcoming)
    status_filter = request.GET.get('status', '')
    today = date.today()
    
    if status_filter == 'past':
        tickets = tickets.filter(booking_date__lt=today)
    elif status_filter == 'today':
        tickets = tickets.filter(booking_date=today)
    elif status_filter == 'upcoming':
        tickets = tickets.filter(booking_date__gt=today)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        tickets = tickets.filter(
            Q(customer_name__icontains=search_query) |
            Q(place__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Hitung jumlah tiket untuk setiap status
    past_count = Ticket.objects.filter(booking_date__lt=today).count()
    today_count = Ticket.objects.filter(booking_date=today).count()
    upcoming_count = Ticket.objects.filter(booking_date__gt=today).count()
    
    context = {
        'tickets': tickets,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_tickets': tickets.count(),
        'past_count': past_count,
        'today_count': today_count,
        'upcoming_count': upcoming_count,
    }
    return render(request, 'ticket/ticket_list.html', context)


def ticket_create(request):
    """Form untuk membuat/memesan tiket baru"""
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            
            # Optional: Set user jika logged in
            if request.user.is_authenticated:
                ticket.user = request.user
            
            # Harga akan otomatis dikalkulasi di model save()
            ticket.save()
            
            messages.success(
                request, 
                f'Ticket #{ticket.id} successfully booked for {ticket.customer_name}!'
            )
            return redirect('ticket:ticket_list')
        else:
            messages.error(request, 'An error occurred. Please check your form.')
    else:
        form = TicketForm()
    
    context = {
        'form': form,
        'places': Place.objects.all().order_by('name'),
        'is_create': True
    }
    return render(request, 'ticket/ticket_form.html', context)


def ticket_update(request, pk):
    """Edit tiket yang sudah ada"""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()  # Harga akan auto-update di model save()
            messages.success(request, f'Ticket #{ticket.id} successfully updated!')
            return redirect('ticket:ticket_list')
        else:
            messages.error(request, 'An error occurred. Please check your form.')
    else:
        form = TicketForm(instance=ticket)
    
    context = {
        'form': form,
        'ticket': ticket,
        'places': Place.objects.all().order_by('name'),
        'is_create': False
    }
    return render(request, 'ticket/ticket_form.html', context)


def ticket_detail(request, pk):
    """Menampilkan detail lengkap tiket"""
    ticket = get_object_or_404(
        Ticket.objects.select_related('place', 'user'), 
        pk=pk
    )
    
    context = {
        'ticket': ticket
    }
    return render(request, 'ticket/ticket_detail.html', context)


def ticket_delete(request, pk):
    """Hapus tiket"""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        ticket_id = ticket.id
        customer_name = ticket.customer_name
        ticket.delete()
        messages.success(
            request, 
            f'Ticket #{ticket_id} for {customer_name} successfully deleted!'
        )
        return redirect('ticket:ticket_list')
    
    context = {
        'ticket': ticket
    }
    return render(request, 'ticket/ticket_confirm_delete.html', context)


def get_place_price(request, place_id):
   
    try:
        place = Place.objects.get(id=place_id)
        return JsonResponse({
            'success': True,
            'price': float(place.price),
            'name': place.name,
            'description': place.description or '',
            'city': place.city or '',
            'genre': place.genre or ''
        })
    except Place.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Place not found'
        }, status=404)
