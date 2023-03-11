from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.utils import timezone
import requests
from geopy import distance

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from placesapp.models import Place
from placesapp.location_utils import fetch_coordinates


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })

def get_product_restaurants(restaurant_menu_items, order_item):
    """Рестораны, которые могут приготовить продукт из заказа"""
    product_restaurants = [
        rest_item.restaurant for rest_item in restaurant_menu_items
        if rest_item.availability and rest_item.product.id == order_item.product.id
    ]
    return product_restaurants


def get_orders_with_distances():
    orders = Order.objects \
        .exclude(status='D') \
        .prefetch_related('cooking_restaurant', 'items', 'items__product') \
        .order_by('status').calculate_order_total_cost()

    restaurant_menu_items = RestaurantMenuItem.objects.filter(availability=True)\
        .select_related('product', 'restaurant')

    places = Place.objects.filter(
        address__in=[order.address for order in orders] + [rest.address for rest in Restaurant.objects.all()]
    )
    places = {place.address: place for place in places}

    for order in orders:
        order.restaurants = set()
        order.restaurant_distances_flag = True
        for order_item in order.items.all():
            # получаем рестораны, готовые приготовить текущий продукт из заказа
            product_restaurants = get_product_restaurants(
                restaurant_menu_items,
                order_item
            )

            if not order.restaurants:
                order.restaurants = set(product_restaurants)
                continue
            # из полученного списка определяем только рестораны,
            # готовые приготовить и текущий, и остальные продукты
            order.restaurants &= set(product_restaurants)

        order_place = places.get(order.address)
        order_coords = order_place.latitude, order_place.longitude
        if None in order_coords:
            # флаг будет использован в шаблоне для
            # информирования о невозможности определения координат
            order.restaurant_distances_flag = False
        else:
            # если удалось определить координаты, считаем растояния до каждого ресторана
            restaurant_distances = []
            for restaurant in order.restaurants:
                restaurant_place = places.get(restaurant.address)
                restaurant_coords = restaurant_place.latitude, restaurant_place.longitude

                restaurant_distance = round(
                    distance.distance(order_coords, restaurant_coords).km, 2
                )

                restaurant_distances.append([restaurant.name, restaurant_distance])
            restaurant_distances.sort(key=lambda x: x[1])
            order.restaurant_distances = restaurant_distances
    return orders


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = get_orders_with_distances()
    return render(
        request,
        template_name='order_items.html',
        context={'order_items': orders, 'path': request.path}
    )
