from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    # page stuff
    path('', views.show_activities, name='my_activities'),
    # path('<uuid:id>/', views.view_activity, name='view_activity'),

    # AJAX stuff
    path('edit/<uuid:actid>',views.edit_activity_ajax,name='edit_activity'),
    path('create/', views.create_activity_ajax, name="create_activity"),
    path('delete/<uuid:actid>',views.delete_activity_ajax,name='delete_activity'),
    path('jsonning',views.show_json,name='activity_json_endpoint'),
    path('stats.json', views.stats_json, name='activity_stats_endpoint'),
]