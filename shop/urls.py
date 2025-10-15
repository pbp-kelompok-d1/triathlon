from django.urls import path
from . import views

app_name = 'shop'
urlpatterns = [
    path('', views.show_product, name='shop'),
    path('add/', views.add_product, name='add_product'),
    path('<uuid:id>/', views.product_detail, name='product_detail'),
]