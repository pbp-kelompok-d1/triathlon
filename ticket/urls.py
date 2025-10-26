from django.urls import path
from . import views

app_name = 'ticket'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
<<<<<<< HEAD
    path('<int:id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:id>/edit/', views.ticket_update, name='ticket_update'),
    path('<int:id>/delete/', views.ticket_delete, name='ticket_delete'),
    
    # API endpoints
    path('api/place-price/<int:place_id>/', views.get_place_price, name='get_place_price'),
    path('api/places/', views.place_list_api, name='place_list_api'),
=======
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/edit/', views.ticket_update, name='ticket_update'),
    path('<int:pk>/delete/', views.ticket_delete, name='ticket_delete'),
    
    # API endpoints
    path('api/place-price/<int:place_id>/', views.get_place_price, name='get_place_price'),
>>>>>>> 42ebb9da1ff0472f72649184c37860c99609730f
]