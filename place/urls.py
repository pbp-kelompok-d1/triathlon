from django.urls import path
from . import views

app_name = 'place'

urlpatterns = [
    path("", views.place_list, name="place_list"),
    path("add/", views.add_place, name="add_place"),
    path('<int:pk>/', views.place_detail, name='place_detail'),
    path('<int:pk>/add_review/', views.add_review, name='add_review'),
]
