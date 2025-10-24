from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from place.models import Place

class Ticket(models.Model):
    # Informasi pemesan
    customer_name = models.CharField(
        max_length=200,
        verbose_name="Customer Name",
        default="Unknown"  # tambahkan default agar migrasi aman
    )

    # Relasi ke Place (menggunakan model Place yang sudah ada)
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name="Sport Place",
        null=True,          # biarkan null untuk data lama
        blank=True          # biarkan kosong di form
    )

    # Detail pemesanan
    ticket_quantity = models.PositiveIntegerField(default=1, verbose_name="Ticket Quantity")
    booking_date = models.DateField(verbose_name="Booking Date", default=timezone.now)  # default agar tidak null

    # Harga (auto-calculated)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Total Price", default=0)  # default=0

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    # Optional: User yang memesan
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='my_tickets',
        verbose_name="User"
    )

    class Meta:
        ordering = ['id']
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"Ticket #{self.id} - {self.customer_name} - {self.place.name if self.place else 'No Place'}"

    def save(self, *args, **kwargs):
        # Auto-kalkulasi harga total
        if self.place and self.ticket_quantity:
            self.total_price = self.place.price * self.ticket_quantity
        super().save(*args, **kwargs)

    @property
    def ticket_number(self):
        return f"TK-{str(self.id).zfill(6)}"

    @property
    def status(self):
        from datetime import date
        today = date.today()
        if self.booking_date < today:
            return 'past'
        elif self.booking_date == today:
            return 'today'
        else:
            return 'upcoming'

    @property
    def status_display(self):
        status_map = {
            'past': 'Past',
            'today': 'Today',
            'upcoming': 'Upcoming'
        }
        return status_map.get(self.status, 'Unknown')

    @property
    def status_badge_class(self):
        status_class = {
            'past': 'secondary',
            'today': 'success',
            'upcoming': 'primary'
        }
        return status_class.get(self.status, 'secondary')
