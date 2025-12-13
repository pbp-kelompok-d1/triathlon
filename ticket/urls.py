from django.urls import path
from . import views

app_name = 'ticket'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:id>/', views.ticket_detail, name='ticket_detail'),
    path('<int:id>/edit/', views.ticket_update, name='ticket_update'),
    path('<int:id>/delete/', views.ticket_delete, name='ticket_delete'),

    # API endpoints untuk Flutter
    path('api/tickets/', views.ticket_list_api, name='ticket_list_api'),
    path('api/tickets/create/', views.ticket_create_api, name='ticket_create_api'),
    path('api/<int:id>/', views.ticket_detail_api, name='ticket_detail_api'),
    path('api/<int:id>/update/', views.ticket_update_api, name='ticket_update_api'),
    path('api/<int:id>/delete/', views.ticket_delete_api, name='ticket_delete_api'),
    path('api/place-price/<int:place_id>/', views.get_place_price, name='get_place_price'),
    path('api/places/', views.place_list_api_flutter, name='place_list_api_flutter'),
]