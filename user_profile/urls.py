from django.urls import path
from . import views 
app_name = 'user_profile'

urlpatterns = [
    # Halaman utama profil — otomatis redirect ke dashboard sesuai role
    path('', views.profile_view, name='profile'),

    # Edit profil (hanya data diri, bukan role)
    path('edit/', views.edit_profile, name='edit_profile'),

    # Dashboard per role
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('seller/', views.seller_dashboard, name='seller_dashboard'),
    path('facility-admin/', views.facility_admin_dashboard, name='facility_admin_dashboard'),
]
