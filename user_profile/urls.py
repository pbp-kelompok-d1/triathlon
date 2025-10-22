from django.urls import path
from views import user_dashboard, seller_dashboard, facility_admin_dashboard, profile_view, edit_profile

app_name = 'user_profile'

urlpatterns = [
    # Halaman utama profil — otomatis redirect ke dashboard sesuai role
    path('', profile_view, name='profile'),

    # Edit profil (hanya data diri, bukan role)
    path('edit/', edit_profile, name='edit_profile'),

    # Dashboard per role
    path('user/', user_dashboard, name='user_dashboard'),
    path('seller/', seller_dashboard, name='seller_dashboard'),
    path('facility-admin/', facility_admin_dashboard, name='facility_admin_dashboard'),
]
