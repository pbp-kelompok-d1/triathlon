from django.urls import path
from . import views

app_name = 'shop'
urlpatterns = [
    path('', views.show_product, name='shop'),
    path('add/', views.add_product, name='add_product'),
    path('<uuid:id>/', views.product_detail, name='product_detail'),
    path('<uuid:id>/edit/', views.edit_product, name='edit_product'),
    path('<uuid:id>/delete/', views.delete_product, name='delete_product'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<uuid:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/toggle/<uuid:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('checkout/', views.checkout, name='checkout'),
    path('add_dataset_cycling/', views.load_dataset_cycling, name='load_dataset_cycling'),
    path('add_dataset_running/', views.load_dataset_running, name='load_dataset_running'),
    path('add_dataset_swimming/', views.load_dataset_swimming, name='load_dataset_swimming'),
    #path('delete-products-without-seller/', views.delete_products_without_seller, name='delete_products_without_seller'),
    path('delete-all-products/', views.delete_all_products, name='delete_all_products'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    
    # JSON API endpoints for Flutter
    path('api/products/', views.show_json, name='show_json'),
    path('api/products/mine/', views.show_json_mine, name='show_json_mine'),
    path('api/products/create/', views.create_product_flutter, name='create_product_flutter'),
    path('api/proxy-image/', views.proxy_image, name='proxy_image'),
    path('api/products/<uuid:id>/edit/', views.edit_product, name='edit_product'),
    path('api/products/<uuid:id>/delete/', views.delete_product, name='delete_product'),
    path('api/wishlist/', views.view_wishlist_flutter, name='view_wishlist_flutter'),
    path('api/wishlist/toggle/<uuid:product_id>/', views.toggle_wishlist_flutter, name='toggle_wishlist_flutter'),
    path('api/cart/', views.view_cart_flutter, name='view_cart_flutter'),
    path('api/cart/add/<uuid:product_id>/', views.add_to_cart_flutter, name='add_to_cart_flutter'),
    path('api/cart/remove/<uuid:product_id>/', views.remove_from_cart_flutter, name='remove_from_cart_flutter'),
    path('api/checkout/', views.checkout_flutter, name='checkout_flutter'),
    path('api/cart/update/<int:item_id>/', views.update_cart_quantity_flutter, name='update_cart_quantity_flutter'),
    path('api/wishlist/check/<uuid:product_id>/', views.check_wishlist_status_flutter, name='api_check_wishlist'),
]