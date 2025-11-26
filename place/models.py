from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


GENRE_CHOICES = [
    ('Swimming Pool', 'Swimming Pool'),   
    ('Running Track', 'Running Track'),
    ('Bicycle Tracking', 'Bicycle Tracking'),
]


class Place(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    city = models.CharField(max_length=100, null=True)
    province = models.CharField(max_length=100, null=True)
    

    genre = models.CharField(
        max_length=100, 
        choices=GENRE_CHOICES, 
        null=True, 
        blank=True,  
        default=None
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='places/', null=True, blank=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='administered_places', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

class Review(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.place.name}"
