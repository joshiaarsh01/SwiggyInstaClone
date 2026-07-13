from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('brand/<int:brand_id>/', views.brand_products, name='brand_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<str:item_type>/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('remove-from-cart/<str:key>/', views.remove_from_cart, name='remove_from_cart'),
    path('increase-qty/<str:key>/', views.increase_qty, name='increase_qty'),
    path('decrease-qty/<str:key>/', views.decrease_qty, name='decrease_qty'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('add-to-wishlist/<str:item_type>/<int:item_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<str:key>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('toggle-wishlist/<str:item_type>/<int:item_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/<int:customer_id>/', views.verify_otp, name='verify_otp'),
]