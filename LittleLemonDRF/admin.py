from django.contrib import admin
from .models import Rating, MenuItem, Category, Item_otd, Order, OrderItem, Cart
# Register your models here.
admin.site.register(MenuItem)
admin.site.register(Category)
admin.site.register(Rating)
admin.site.register(Item_otd)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Cart)