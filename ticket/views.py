from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import date
from .models import Ticket
from .forms import TicketForm
from place.models import Place

def ticket_list(request):
    tickets = Ticket.objects.select_related('place', 'user').all()
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    today = date.today()

    if status_filter == 'past':
        tickets = tickets.filter(booking_date__lt=today)
    elif status_filter == 'today':
        tickets = tickets.filter(booking_date=today)
    elif status_filter == 'upcoming':
        tickets = tickets.filter(booking_date__gt=today)

    if search_query:
        tickets = tickets.filter(
            Q(customer_name__icontains=search_query) |
            Q(place__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    past_count = Ticket.objects.filter(booking_date__lt=today).count()
    today_count = Ticket.objects.filter(booking_date=today).count()
    upcoming_count = Ticket.objects.filter(booking_date__gt=today).count()

    # Jika request dari AJAX, kirim data JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = list(tickets.values(
            'id', 'customer_name', 'place__name', 'booking_date', 'total_price'
        ))
        return JsonResponse({'tickets': data})

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
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
            ticket.save()

            # Jika AJAX request, kirim JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Ticket #{ticket.id} successfully booked!',
                    'ticket': {
                        'id': ticket.id,
                        'customer_name': ticket.customer_name,
                        'place': ticket.place.name,
                        'booking_date': ticket.booking_date.strftime('%Y-%m-%d'),
                        'total_price': float(ticket.total_price)
                    }
                })

            messages.success(request, f'Ticket #{ticket.id} successfully booked!')
            return redirect('ticket:ticket_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)

            messages.error(request, 'Please check your form.')
    else:
        form = TicketForm()

    context = {
        'form': form,
        'places': Place.objects.all().order_by('name'),
        'is_create': True
    }
    return render(request, 'ticket/ticket_form.html', context)


def ticket_update(request, pk):
    """Edit an existing ticket, with AJAX support."""
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'Ticket #{ticket.id} updated successfully!'})
            messages.success(request, f'Ticket #{ticket.id} successfully updated!')
            return redirect('ticket:ticket_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            messages.error(request, 'An error occurred. Please check the form.')
    else:
        form = TicketForm(instance=ticket)
    
    context = {
        'form': form,
        'ticket': ticket,
        'is_create': False
    }
    return render(request, 'ticket/ticket_form.html', context)

def ticket_delete(request, pk):
    """Delete a ticket with AJAX support."""
    ticket = get_object_or_404(Ticket, pk=pk)
    
    # Handle AJAX DELETE request
    if request.method == 'DELETE':
        try:
            ticket_id = ticket.id
            ticket.delete()
            return JsonResponse({'success': True, 'message': f'Ticket #{ticket_id} has been deleted.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # Fallback for standard POST request
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, f'Ticket #{ticket.id} successfully deleted!')
        return redirect('ticket:ticket_list')
    
    # Render confirmation page for GET request
    return render(request, 'ticket/ticket_confirm_delete.html', {'ticket': ticket})


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
