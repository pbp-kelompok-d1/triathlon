from django.urls import path
from . import views

app_name = 'shop'
urlpatterns = [
    path('', views.show_product, name='shop'),
    path('add/', views.add_product, name='add_product'),
    path('<uuid:id>/', views.product_detail, name='product_detail'),
    path('<uuid:id>/edit/', views.edit_product, name='edit_product'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<uuid:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/toggle/<uuid:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('checkout/', views.checkout, name='checkout'),

    
]