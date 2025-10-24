from django.urls import path
from . import views 
app_name = 'user_profile'

urlpatterns = [
    # Halaman utama profil — otomatis redirect ke dashboard sesuai role
    path('', views.dashboard_shell_view, name='profile'),

    # Edit profil (hanya data diri, bukan role)
    path('edit/', views.edit_profile, name='edit_profile'),
    path('profile/change_password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_user_account, name='delete_account'),
    
    # Dashboard per role
    path('get_content/', views.get_dashboard_content, name='get_dashboard_content'),
]
