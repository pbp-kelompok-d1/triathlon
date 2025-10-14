from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.show_forums, name='forums'),
    path('create/', views.create_forum_post, name='create_post'),
    path('<uuid:id>/', views.post_detail, name='post_detail'),
    path('<uuid:post_id>/reply/', views.add_reply, name='add_reply'),
]