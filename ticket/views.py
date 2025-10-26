from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import date
from .models import Ticket
from .forms import TicketForm
<<<<<<< HEAD
from django.contrib.auth.decorators import login_required
from place.models import Place
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
=======
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
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f

@login_required
def ticket_list(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Please complete your profile first.')
        return redirect('account:profile')
    
    if request.user.profile.is_admin():
        tickets = Ticket.objects.select_related('place', 'user_profile').all()
    else:
        tickets = Ticket.objects.select_related('place', 'user_profile').filter(
            user_profile=request.user.profile
        )
    
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    today = date.today()

<<<<<<< HEAD
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

    if request.user.profile.is_admin():
        user_tickets = Ticket.objects.all()
    else:
        user_tickets = Ticket.objects.filter(user_profile=request.user.profile)
    
    past_count = user_tickets.filter(booking_date__lt=today).count()
    today_count = user_tickets.filter(booking_date=today).count()
    upcoming_count = user_tickets.filter(booking_date__gt=today).count()

    places = Place.objects.all().order_by('name')

    context = {
        'tickets': tickets,
        'places': places,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_tickets': tickets.count(),
        'past_count': past_count,
        'today_count': today_count,
        'upcoming_count': upcoming_count,
    }
    return render(request, 'ticket/ticket_list.html', context)

@login_required
def ticket_create(request):
    place_id = request.GET.get('place_id', None)
    
=======
def ticket_create(request):
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
<<<<<<< HEAD
            
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                ticket.user_profile = request.user.profile
            
            ticket.total_price = ticket.place.price * ticket.ticket_quantity
            ticket.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Ticket #{ticket.id} successfully booked!',
                    'toast': {
                        'title': 'Booking Success!',
                        'message': f'Ticket #{ticket.id} for {ticket.place.name} has been created',
                        'type': 'success'
                    },
                    'ticket': {
                        'id': ticket.id,
                        'customer_name': ticket.customer_name,
                        'place': ticket.place.name,
                        'booking_date': ticket.booking_date.strftime('%Y-%m-%d'),
                        'ticket_quantity': ticket.ticket_quantity,
                        'total_price': float(ticket.total_price)
                    }
                })

            messages.success(request, f'Ticket #{ticket.id} successfully booked!')
            return redirect('ticket:ticket_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'toast': {
                        'title': 'Booking Failed',
                        'message': 'Please check your form and try again',
                        'type': 'error'
                    }
                }, status=400)
            messages.error(request, 'Please check your form.')
    else:
        if place_id:
            form = TicketForm(initial={'place': place_id})
        else:
            form = TicketForm()

    places = Place.objects.all().order_by('name')
    
    selected_place = None
    if place_id:
        try:
            selected_place = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            pass
    
    context = {
        'form': form,
        'places': places,
        'selected_place': selected_place,
        'is_create': True
    }
    return render(request, 'ticket/ticket_form.html', context)

@login_required
def ticket_update(request, id):
    ticket = get_object_or_404(Ticket, id=id)
    
    is_owner = ticket.user_profile == request.user.profile
    is_admin = request.user.profile.is_admin()
    
    if not (is_owner or is_admin):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to edit this ticket.',
                'toast': {
                    'title': 'Access Denied',
                    'message': 'You do not have permission to edit this ticket',
                    'type': 'error'
                }
            }, status=403)
        messages.error(request, 'You do not have permission to edit this ticket.')
        return redirect('ticket:ticket_list')
    
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.total_price = ticket.place.price * ticket.ticket_quantity
            ticket.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': f'Ticket #{ticket.id} updated successfully!',
                    'toast': {
                        'title': 'Update Success!',
                        'message': f'Ticket #{ticket.id} has been updated successfully',
                        'type': 'success'
                    },
                    'ticket': {
                        'id': ticket.id,
                        'customer_name': ticket.customer_name,
                        'place': ticket.place.name,
                        'booking_date': ticket.booking_date.strftime('%Y-%m-%d'),
                        'ticket_quantity': ticket.ticket_quantity,
                        'total_price': float(ticket.total_price)
                    }
                })
            messages.success(request, f'Ticket #{ticket.id} successfully updated!')
            return redirect('ticket:ticket_list')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'toast': {
                        'title': 'Update Failed',
                        'message': 'Please check your form and try again',
                        'type': 'error'
                    }
                }, status=400)
            messages.error(request, 'An error occurred. Please check the form.')
    else:
        form = TicketForm(instance=ticket)
    
    places = Place.objects.all().order_by('name')
    
    context = {
        'form': form,
        'ticket': ticket,
        'places': places,
=======
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
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
        'is_create': False
    }
    return render(request, 'ticket/ticket_form.html', context)

<<<<<<< HEAD
@login_required
@require_POST
def ticket_delete(request, id):  
    ticket = get_object_or_404(Ticket, pk=id)
    
    is_owner = ticket.user_profile == request.user.profile
    is_admin = request.user.profile.is_admin()
    
    if not (is_owner or is_admin):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete this ticket.',
                'toast': {
                    'title': 'Access Denied',
                    'message': 'You do not have permission to delete this ticket',
                    'type': 'error'
                }
            }, status=403)
        messages.error(request, 'You do not have permission to delete this ticket.')
        return redirect('ticket:ticket_list')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            ticket_id = ticket.id
            place_name = ticket.place.name
            ticket.delete()
            return JsonResponse({
                'success': True,
                'message': f'Ticket #{ticket_id} has been deleted.',
                'toast': {
                    'title': 'Delete Success!',
                    'message': f'Ticket #{ticket_id} for {place_name} has been deleted',
                    'type': 'success'
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e),
                'toast': {
                    'title': 'Delete Failed',
                    'message': 'An error occurred while deleting the ticket',
                    'type': 'error'
                }
            }, status=500)

    ticket.delete()
    messages.success(request, f'Ticket #{ticket.id} successfully deleted!')
    return redirect('ticket:ticket_list')

@login_required
def ticket_detail(request, id):
    ticket = get_object_or_404(
        Ticket.objects.select_related('user_profile', 'place'),
        pk=id
    )
    
    is_owner = ticket.user_profile == request.user.profile
    is_admin = request.user.profile.is_admin()
    
    if not (is_owner or is_admin):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('ticket:ticket_list')
    
    context = {'ticket': ticket}
    return render(request, 'ticket/ticket_detail.html', context)

@login_required
def get_place_price(request, place_id):
=======
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
   
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
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
<<<<<<< HEAD

@login_required
def place_list_api(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        places = Place.objects.all().values('id', 'name', 'price')
        return JsonResponse({'places': list(places)})
    return JsonResponse({'error': 'Invalid request'}, status=400)

=======
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
