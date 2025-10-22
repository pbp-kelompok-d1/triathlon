from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    place_id = models.IntegerField()
    place_name = models.CharField(max_length=200)
    booking_date = models.DateTimeField(auto_now_add=True)
    visit_date = models.DateField()
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price_per_ticket = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.price_per_ticket * self.quantity
        super().save(*args, **kwargs)

    def is_upcoming(self):
        return self.visit_date >= timezone.now().date()

    def __str__(self):
        return f"{self.user.username} - {self.place_name}"