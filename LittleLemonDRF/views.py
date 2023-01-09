from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.decorators import throttle_classes


class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'inventory']
    filterset_fields = ['price', 'inventory']
    search_fields = ['title']

class RatingsView(generics.ListCreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    def get_permissions(self):
        if (self.request.method == 'GET'):
         return []
        return [IsAuthenticated()]

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def menu_items(request):
    if(request.method=='GET'):
        items = MenuItem.objects.select_related('category').all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_parms.get('search')
        ordering = request.query_params.get('ordering')
        if category_name:
            items = items.filter(category_title = category_name)
        if to_price:
            items = items.filter(price=to_price)
        if search:
            items = items.filter(title_contains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            items = items.order_by(*ordering)
        serialized_item = MenuItemserializer(items, many=True)
        return Response(serialized_item.data)
    elif request.method=='POST':
        if request.user.group.filter(name='Manager').exists():
            serialized_item = MenuItemSerializer(data=request.data)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.validated_data, status.HTTP_201_CREATED) 
        else:
            return Respones({'message': 'You do not have authorization to add items sorry'}, 403)

@api_view(['GET','DELETE','PUT'])
def single_item (request, id):
    if request.method == 'GET':
        item = get_object_or_404(MenuItem,pk=id)
        serialized_item = MenuItemSerializer(item,context={'request': request})
        return Response (serialized_item.data,status.HTTP_200_OK)
    elif request.method == 'DELETE':
        if request.user.groups.filter(name= 'Manager').exists () :
            item = MenuItem.objects.get(pk=id)
            item.delete()
            serialized_item = MenuItemSerializer(item,context={'request': request})
            return Response (serialized_item.data,status.HTTP_200_OK)
        else:
            return Response ({"message": "You are not authorized"}, status.HTTP_401_UNAUTHORIZED)
    elif request.method == 'PUT':
        if request.user.groups.filter(name= 'Manager').exists () :
            item = MenuItem.objects.get(pk=id)
            item.title=request.data['title']
            item.price=request.data['price']
            serialized_item = MenuItemSerializer(item,context={'request': request})
            return Response (serialized_item.data,status.HTTP_200_OK)
        else:
            return Response ({"message": "You are not authorized"}, status.HTTP_401_UNAUTHORIZED)
           

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order(request):
    if(request.method=='GET'):
        orders = Cart.objects.get()
        serialized_item = CartSerializer(items, many=True)
        return Response(serialized_item.data)


@api_view()
def item_otdView(request):
    data = Item_otd.objects.get()
    id = data.menuitem_id
    item = MenuItem.objects.get(pk=id)
    serialized_item = MenuItemSerializer(item)
    return Response(serialized_item.data)


@api_view(['POST','DELETE','GET'])
@permission_classes([IsAuthenticated])
def cart_items(request):
    current_user = request.user.id
    user = User.objects.get(id=current_user)
    if request.method == 'POST':
        if Cart.objects.filter(user = current_user).exists():
            cart = Cart.objects.get(user = current_user)
            menu_item = MenuItem.objects.get(id = request.data['menuitem'])
            cart.menuitem = menu_item
            cart.unit_price = menu_item.price
            cart.price = menu_item.price * Decimal(request.data['quantity'])
            cart.quantity = request.data['quantity']
            cart.save()
            serialized_cart = CartSerializer(cart)
            return Response(serialized_cart.data,status.HTTP_201_CREATED) 
        else:
            menu_item = MenuItem.objects.get(id = request.data['menuitem'])
            price = menu_item.price * Decimal(request.data['quantity'])
            cart = Cart.objects.create(user = user,menuitem= menu_item, unit_price=menu_item.price,price=price,quantity=request.data['quantity'])
            return Response ({"message": "cart created"},status.HTTP_201_CREATED)
    elif request.method == 'GET':
        if Cart.objects.filter(user = current_user).exists():
            cart = Cart.objects.get(user = current_user)
            serialized_cart = CartSerializer(cart)
            return Response(serialized_cart.data,status.HTTP_200_OK) 
        else:
            return Response ({"message": "cart is empty"},status.HTTP_200_OK)
    elif request.method == 'DELETE':
        Cart.objects.filter(user = current_user).delete()
        return Response ({"message": "items are deleted and cart is empty"},status.HTTP_200_OK)
    

@api_view(['POST','DELETE','GET','PATCH'])
@permission_classes([IsAuthenticated])
def orders(request):
    if request.user.groups.filter(name= 'Manager').exists () :
        if request.method == 'GET': 
            orders = Order.objects.all()
            serialized_orders = Orderserializer(orders)
            return Response(serialized_orders.data,status.HTTP_200_OK) 
    elif request.user.groups.filter(name= 'Delivery').exists() :
        if request.method == 'GET': 
            current_user = request.user.id
            user = User.objects.get(id=current_user)
            if Order.objects.filter(user=current_user).exists() :
                orders = Order.objects.filter(user=current_user).all()
                serialized_orders = Orderserializer(orders)
                return Response(serialized_orders.data,status.HTTP_200_OK) 
            else:
                return Response ({"message": "you have no orders to deliver"},status.HTTP_200_OK)
    else:
        current_user = request.user.id
        user = User.objects.get(id=current_user)
        if request.method == 'POST':
            if Cart.objects.filter(user = current_user).exists():
                cart_items =  Cart.objects.get(user = user)
                order = Order.objects.create(user = user, total=cart_items.price)
                order.save()
                get_order = Order.objects.get(user = user)
                order_item = OrderItem.objects.create(order = Order.objects.get(user = user),
                                                      menuitem = cart_items.menuitem, 
                                                      quantity=cart_items.quantity,
                                                      unit_price=cart_items.unit_price,
                                                      price=cart_items.price)
                order_item.save()
                Cart.objects.filter(user = current_user).delete()
                serialized_order_item = OrderItemserializer(order_item)
                return Response(serialized_order_item.data,status.HTTP_201_CREATED) 
            else: 
                return Response ({"message": "can not make order beacuse cart is empty"},status.HTTP_200_OK)
        elif request.method == 'GET':
            current_user = request.user.id
            user = User.objects.get(id = current_user)
            if Order.objects.filter(user_id = user).exists():
                orders = Order.objects.filter(user_id = user).all()
                serialized_orders = Orderserializer(orders)
                return Response(serialized_orders.data,status.HTTP_200_OK) 
            else:
                return Response ({"message": "you have no orders right now!"},status.HTTP_200_OK)
        elif request.method == 'DELETE':
            Cart.objects.filter(user = current_user).delete()
            return Response ({"message": "items are deleted and cart is empty"},status.HTTP_200_OK)
    

@api_view(['POST','DELETE','GET','PATCH'])
@permission_classes([IsAuthenticated])
def order_single(request,id):
    if request.user.groups.filter(name= 'Manager').exists () :
        if request.method == 'POST': 
            order = Order.objects.get(id=id)
            order.delivery_crew = request.data['delivery_crew']
            serialized_orders = Orderserializer(order)
            return Response(serialized_orders.data,status.HTTP_200_OK) 
        if request.method == 'DELETE': 
            Order.objects.filter(id = id).delete()
            return Response ({"message": "order is deleted "},status.HTTP_200_OK)
    elif request.user.groups.filter(name= 'Delivery').exists() :
        if request.method == 'PATCH': 
            if Order.objects.filter(id=id).exists() :
                order = Order.objects.get(id=id)
                order.status = 1
                order.save()
                serialized_orders = Orderserializer(orders)
                return Response(serialized_orders.data,status.HTTP_200_OK) 
            else:
                return Response ({"message": "you have no orders to deliver"},status.HTTP_200_OK)
    else:
        current_user = request.user.id
        user = User.objects.get(id=current_user)
        if request.method == 'GET':
            current_user = request.user.id
            user = User.objects.get(id=current_user)
            if Order.objects.filter(user = current_user).exists():
                order = Order.objects.filter(id=id).all()
                if order.user == current_user:
                    order_items = OrderItem.objects.filter(order=id).all()
                    serialized_order_items = OrderItemserializer(order_items)
                    return Response(serialized_order_items.data,status.HTTP_200_OK) 
                else:
                    return Response ({"message": "not your order"},status.HTTP_404_NOT_FOUND)
            else:
                return Response ({"message": "you have no orders right now!"},status.HTTP_200_OK)

@api_view(['POST','DELETE','GET'])
@permission_classes([IsAdminUser])
@throttle_classes([AnonRateThrottle])
def managers (request):
    if request.method =="GET":
        managers = User.objects.filter(groups = 1)
        serialized_users = UserSerializer(managers, many=True)
        return Response(serialized_users.data) 
    return Response({"message": "error"}, status. HTTP_400_BAD_REQUEST)


@api_view(['POST','DELETE','GET'])
@permission_classes([IsAdminUser])
@throttle_classes([UserRateThrottle()])
def managers_single(request,id):
    user = get_object_or_404(User, id=id)
    managers = Group.objects.get(name="Manager")
    if request.method == 'POST':
        managers.user_set.add (user)
        return Response ({"message": "added to the group"},status.HTTP_200_OK)
    elif request.method == 'DELETE':
        managers.user_set.remove (user)
        return Response ({"message": "deleted from mangers"},status.HTTP_200_OK)
    elif request.method == 'GET':
        serialized_user = UserSerializer(user)
        return Response(serialized_user.data,status.HTTP_200_OK) 
    return Response({"message": "error"}, status. HTTP_400_BAD_REQUEST)

@api_view(['POST','DELETE','GET'])
@permission_classes([IsAdminUser])
@throttle_classes([AnonRateThrottle])
def delivery_crew(request):
    if request.method =="GET":
        managers = User.objects.filter(groups = 2)
        serialized_users = UserSerializer(managers, many=True)
        return Response(serialized_users.data) 
    return Response({"message": "error"}, status. HTTP_400_BAD_REQUEST)

@api_view(['POST','DELETE','GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle()])
def delivery_single(request,id):
    user = get_object_or_404(User, id=id)
    managers = Group.objects.get(name="Delivery")
    if request.method == 'POST':
        managers.user_set.add (user)
        return Response ({"message": "added to  delivery "},status.HTTP_200_OK)
    elif request.method == 'DELETE':
        managers.user_set.remove (user)
        return Response ({"message": "deleted from delivery"},status.HTTP_200_OK)
    elif request.method == 'GET':
        serialized_user = UserSerializer(user)
        return Response(serialized_user.data,status.HTTP_200_OK) 
    return Response({"message": "error"}, status. HTTP_400_BAD_REQUEST)


def home(request):
    return render(request,'home.html')

def about(request):
    return render(request, 'about.html')


@api_view(['POST','DELETE','GET'])
@permission_classes([IsAdminUser])
@throttle_classes([AnonRateThrottle])
def throttle_check(request):
    return Response({'message':"successful"})

@api_view()
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def throttle_check_auth(request):
    return Response({'message':"successful"})

