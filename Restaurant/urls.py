from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from . import views

urlpatterns = [
    path('category', views.CategoriesView.as_view()),

    path('menu-items', views.MenuItemsView.as_view()),
    path('menu-items/<int:id>', views.single_item),

    path ('cart/menu-items/', views.cart_items),
    path('orders', views.orders),
    path('orders/<int:id>', views.order_single),

    path('item_otd', views.item_otdView),

    path('ratings', views.RatingsView.as_view),

    path('api-token-auth/', obtain_auth_token),

    path ('groups/manager/users/', views.managers),
    path ('groups/manager/users/<int:id>', views.managers_single),
    path ('groups/delivery_crew/users/', views.delivery_crew),
    path ('groups/delivery_crew/users/<int:id>', views.delivery_single),
    
]
