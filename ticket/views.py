from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from datetime import date
from .models import Ticket
from .forms import TicketForm
from django.contrib.auth.decorators import login_required
from place.models import Place
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

# Fungsi helper untuk mengecek profil, agar tidak duplikat kode
def check_user_profile(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Please complete your profile first.')
        return redirect('account:profile')
    return None

# Fungsi helper untuk merespon 'Permission Denied' ke AJAX
def ajax_permission_denied(message="Permission Denied"):
    return JsonResponse({
        'success': False,
        'message': message,
        'toast': {
            'title': 'Access Denied',
            'message': message,
            'type': 'error'
        }
    }, status=403)

@login_required
def ticket_list(request):
    profile_redirect = check_user_profile(request)
    if profile_redirect:
        return profile_redirect
    
    # Tentukan base queryset SEKALI
    if request.user.profile.is_admin():
        # Admin melihat semua tiket
        base_tickets = Ticket.objects.select_related('place', 'user').all()
    else:
        # User biasa hanya melihat tiket milik MEREKA (via 'user')
        base_tickets = Ticket.objects.select_related('place', 'user').filter(
            user=request.user 
        )
    
    # Hitung statistik dari base queryset (sebelum difilter)
    today = date.today()
    past_count = base_tickets.filter(booking_date__lt=today).count()
    today_count = base_tickets.filter(booking_date=today).count()
    upcoming_count = base_tickets.filter(booking_date__gt=today).count()

    # Terapkan filter status dan pencarian
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Gunakan 'tickets' untuk hasil yang sudah difilter
    tickets = base_tickets 

    if status_filter == 'past':
        tickets = tickets.filter(booking_date__lt=today)
    elif status_filter == 'today':
        tickets = tickets.filter(booking_date=today)
    elif status_filter == 'upcoming':
        tickets = tickets.filter(booking_date__gt=today)

    if search_query:
        # Buat query pencarian
        q_filters = Q(customer_name__icontains=search_query) | \
                    Q(place__name__icontains=search_query)
        
        # Perbaikan untuk pencarian ID: 'icontains' gagal pada integer.
        if search_query.isdigit():
             q_filters |= Q(id=search_query)
             
        tickets = tickets.filter(q_filters)

    places = Place.objects.all().order_by('name')

    context = {
        # Gunakan 'tickets' yang sudah difilter dan diurutkan
        'tickets': tickets.order_by('-booking_date', '-id'), 
        'places': places,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_tickets': tickets.count(), # Total dari hasil filter
        'past_count': past_count,
        'today_count': today_count,
        'upcoming_count': upcoming_count,
    }
    return render(request, 'ticket/ticket_list.html', context)

@login_required
def ticket_create(request):
    profile_redirect = check_user_profile(request)
    if profile_redirect:
        # Jika user belum punya profil, kirim error
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ajax_permission_denied('Please complete your profile first.')
        return profile_redirect

    place_id = request.GET.get('place_id', None)
    
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)

            ticket.user = request.user 
            
            ticket.total_price = ticket.place.price * ticket.ticket_quantity
            ticket.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
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
            # Fallback untuk non-AJAX
            messages.success(request, f'Ticket #{ticket.id} successfully booked!')
            return redirect('ticket:ticket_list')
        else:
            # Form tidak valid
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'toast': {
                        'title': 'Booking Failed',
                        'message': 'Please check your form and try again',
                        'type': 'error'
                    }
                }, status=400)
            # Fallback untuk non-AJAX
            messages.error(request, 'Please check your form.')
    
    # Bagian GET request (jika diakses langsung, bukan via modal)
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
    profile_redirect = check_user_profile(request)
    if profile_redirect:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ajax_permission_denied('Please complete your profile first.')
        return profile_redirect

    ticket = get_object_or_404(Ticket, id=id)
    is_owner = ticket.user == request.user
    is_admin = request.user.profile.is_admin()

    if not (is_owner or is_admin):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ajax_permission_denied('You do not have permission to edit this ticket.')
        messages.error(request, 'You do not have permission to edit this ticket.')
        return redirect('ticket:ticket_list')

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.total_price = ticket.place.price * ticket.ticket_quantity
            ticket.save()


            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Ticket #{ticket.id} successfully updated!',
                    'toast': {
                        'title': 'Update Success!',
                        'message': f'Ticket #{ticket.id} for {ticket.place.name} has been updated',
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
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'toast': {
                        'title': 'Update Failed',
                        'message': 'Please check your form and try again.',
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
        'is_create': False
    }
    return render(request, 'ticket/ticket_form.html', context)


@login_required
@require_POST
def ticket_delete(request, id):
    profile_redirect = check_user_profile(request)
    if profile_redirect:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ajax_permission_denied('Please complete your profile first.')
        return profile_redirect
 
    ticket = get_object_or_404(Ticket, pk=id)
    
    is_owner = ticket.user == request.user
    is_admin = request.user.profile.is_admin()
    
    if not (is_owner or is_admin):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ajax_permission_denied('You do not have permission to delete this ticket.')
        messages.error(request, 'You do not have permission to delete this ticket.')
        return redirect('ticket:ticket_list')

    try:
        ticket_id = ticket.id
        place_name = ticket.place.name
        ticket.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Ticket #{ticket_id} has been deleted.',
                'toast': {
                    'title': 'Delete Success!',
                    'message': f'Ticket #{ticket_id} for {place_name} has been deleted',
                    'type': 'success'
                }
            })
        messages.success(request, f'Ticket #{ticket_id} successfully deleted!')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 'message': str(e),
                'toast': { 'title': 'Delete Failed', 'message': 'An error occurred', 'type': 'error' }
            }, status=500)
        messages.error(request, 'An error occurred while deleting the ticket.')

    return redirect('ticket:ticket_list')

@login_required
def ticket_detail(request, id):
    profile_redirect = check_user_profile(request)
    if profile_redirect:
        return profile_redirect
        
    ticket = get_object_or_404(
        Ticket.objects.select_related('user', 'place'),
        pk=id
    )
    
    is_owner = ticket.user == request.user
    is_admin = request.user.profile.is_admin()
    
    if not (is_owner or is_admin):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('ticket:ticket_list')
    
    context = {'ticket': ticket}
    return render(request, 'ticket/ticket_detail.html', context)

@login_required
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

@login_required
def place_list_api(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        places = Place.objects.all().values('id', 'name', 'price')
        return JsonResponse({'places': list(places)})
    return JsonResponse({'error': 'Invalid request'}, status=400)