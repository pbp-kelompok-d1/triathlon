from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    
    # Extended user profile untuk menambahkan role dan informasi tambahan
    
    ROLE_CHOICES = [
        ('USER', 'User'),
        ('ADMIN', 'Admin'),
        ('SELLER', 'Seller'),
        ('FACILITY_ADMIN', 'Facility Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    # Permission checks
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_seller(self):
        return self.role == 'SELLER'
    
    def is_facility_admin(self):
        return self.role == 'FACILITY_ADMIN'
    
    def is_regular_user(self):
        return self.role == 'USER'
    
    def can_manage_forum(self):
        return self.role in ['ADMIN']
    
    def can_manage_shop(self):
        return self.role in ['ADMIN', 'SELLER']
    
    def can_manage_tickets(self):
        return self.role in ['ADMIN']
    
    def can_manage_facilities(self):
        return self.role in ['ADMIN', 'FACILITY_ADMIN']


# Signal to automatically create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    if created:
        UserProfile.objects.create(user=instance)
