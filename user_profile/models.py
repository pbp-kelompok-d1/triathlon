from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    # Pilihan role yang tersedia
    ROLE_CHOICES = [
        ('USER', 'User'),
        ('ADMIN', 'Admin'),
        ('SELLER', 'Seller'),
        ('FACILITY_ADMIN', 'Facility Administrator'),
    ]

    # Relasi ke model User bawaan Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Menyimpan role aktif user
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')

    # Info tambahan
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def switch_role(self, new_role):
        """Ganti role aktif user (switch role)."""
        valid_roles = [choice[0] for choice in self.ROLE_CHOICES]
        if new_role in valid_roles:
            self.role = new_role
            self.save()
            return True
        return False

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_seller(self):
        return self.role == 'SELLER'

    def is_facility_admin(self):
        return self.role == 'FACILITY_ADMIN'

    def is_regular_user(self):
        return self.role == 'USER'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Otomatis buat profil setelah user dibuat."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Simpan profil setiap kali user di-update."""
    instance.profile.save()
