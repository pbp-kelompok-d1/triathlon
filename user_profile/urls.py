from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static
app_name = 'user_profile'

urlpatterns = [
    # Halaman utama profil — otomatis redirect ke dashboard sesuai role
    path('', views.dashboard_shell_view, name='profile'),

    # Edit profil (hanya data diri, bukan role)
    path('edit/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('delete-account/', views.delete_user_account, name='delete_account'),
    
    # Dashboard per role
    path('get_content/', views.get_dashboard_content, name='get_dashboard_content'),

    # Admin Dashboard
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/ajax/get-user-list/', views.get_admin_user_list, name='get_admin_user_list'),
    path('admin/ajax/update-user/', views.admin_update_user_view, name='admin_update_user'),
    path('admin/ajax/delete-user/', views.admin_delete_user_view, name='admin_delete_user'),
    
    # API Endpoints
    path('api/current-user/', views.get_current_user_api, name='api_current_user'),
    path('api/edit/', views.edit_profile_api, name='api_edit_profile'),
    path('api/change-password/', views.change_password_api, name='api_change_password'),
    path('api/delete-account/', views.delete_user_account_api, name='api_delete_account'),
    path('api/dashboard/', views.get_dashboard_data_api, name='api_dashboard'),
    path('api/admin/users/', views.get_admin_user_list_api, name='api_admin_list'),
    path('api/admin/update/', views.admin_update_user_api, name='api_admin_update'),
    path('api/admin/delete/', views.admin_delete_user_api, name='api_admin_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)