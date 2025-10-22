from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Ticket
from .forms import TicketForm


def book_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user  # otomatis isi user aktif
            ticket.save()
            messages.success(request, f"Tiket berhasil dipesan untuk {ticket.place_name} pada {ticket.visit_date}.")
            return redirect('ticket_success')  # arahkan ke halaman sukses (atau daftar tiket)
    else:
        form = TicketForm()

    return render(request, 'booking.html', {'form': form})

def ticket_list(request):
    query = request.GET.get('q')
    if query:
        ticket = Ticket.objects.filter(name__icontains=query)
    else:
        ticket = Ticket.objects.all()
    return render(request, 'ticket_list.html', {'ticket': ticket})
