from django.urls import path
from . import views

app_name = 'ticket'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/edit/', views.ticket_update, name='ticket_update'),
    path('<int:pk>/delete/', views.ticket_delete, name='ticket_delete'),
    
    # API endpoints
    path('api/place-price/<int:place_id>/', views.get_place_price, name='get_place_price'),
]