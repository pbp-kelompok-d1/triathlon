from django.urls import path,include
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

app_name = 'place'

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.place_list, name="place_list"),
    path("add/", views.add_place, name="add_place"),
    path('<int:pk>/', views.place_detail, name='place_detail'),
    path('<int:place_id>/', views.place_detail, name='place_detail'),
    path('add_review/<int:pk>/', views.add_review, name='add_review'),
    path('<int:pk>/edit/', views.edit_place, name='edit_place'),
    path('<int:pk>/delete/', views.delete_place, name='delete_place'),
    path('<int:pk>/delete-image/', views.delete_image, name='delete_image'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    # URL untuk trigger loading data
    path('load/cycling/', views.load_places_cycling, name='load_cycling'),
    path('load/running/', views.load_places_running, name='load_running'),
    path('load/swimming/', views.load_places_swimming, name='load_swimming'),
    

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)