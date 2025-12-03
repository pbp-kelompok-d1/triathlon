from django.urls import path,include
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

app_name = 'place'

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.place_list, name="place_list"),
    path("add/", views.add_place, name="add_place"),
    path('<int:pk>/', views.place_detail, name='place_detail'),
    path('<int:place_id>/', views.place_detail, name='place_detail'),
    path('<int:pk>/add_review/', csrf_exempt(views.add_review), name='add_review'),
    path('review/<int:review_id>/delete/', csrf_exempt(views.delete_review), name='delete_review'),
    path('<int:pk>/edit/', views.edit_place, name='edit_place'),
    path('<int:pk>/delete/', views.delete_place, name='delete_place'),
    path('<int:pk>/delete-image/', views.delete_image, name='delete_image'),
    # URL untuk trigger loading data
    path('load/cycling/', views.load_places_cycling, name='load_cycling'),
    path('load/running/', views.load_places_running, name='load_running'),
    path('load/swimming/', views.load_places_swimming, name='load_swimming'),
    
    path('api/places/', views.api_place_list, name='api_place_list'),
    path('api/places/<int:pk>/', views.api_place_detail, name='api_place_detail'),
    path('api/places/<int:pk>/reviews/', views.api_place_reviews, name='api_place_reviews'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)