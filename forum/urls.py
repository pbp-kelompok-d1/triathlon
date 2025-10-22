from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.show_forums, name='forums'),
    path('create/', views.create_forum_post, name='create_post'),
    path('<uuid:id>/', views.post_detail, name='post_detail'),
    path('<uuid:post_id>/reply/', views.add_reply, name='add_reply'),
    
    # AJAX endpoints
    path('json/', views.show_json, name='show_json'),
    path('ajax/add/', views.add_post_ajax, name='add_post_ajax'),
    path('<uuid:post_id>/edit/', views.edit_post_ajax, name='edit_post_ajax'),
    path('<uuid:post_id>/delete/', views.delete_post, name='delete_post'),
    path('reply/<uuid:reply_id>/delete/', views.delete_reply, name='delete_reply'),
]