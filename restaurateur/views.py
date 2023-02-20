from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone
import requests
from geopy import distance

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from placesapp.models import Place


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


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_place_coords(address):
    geocoder_key = settings.YA_GEOCODER_API_KEY

    place, created = Place.objects.get_or_create(
        address=address,
    )

    if not created:
        return place.longitude, place.latitude

    place_coords = fetch_coordinates(
        geocoder_key, address
    )

    if not place_coords:
        place.delete()
        return None

    place.longitude, place.latitude = place_coords
    place.update_time = timezone.now()
    place.save()
    return place.latitude, place.longitude


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.annotate(total_cost=Sum('order_items__price'))\
        .exclude(status='D')\
        .prefetch_related('restaurant', 'order_items', 'order_items__product')\
        .order_by('status')

    restaurant_menu_items = RestaurantMenuItem.objects.filter(availability=True)\
        .select_related('product', 'restaurant')

    for order in orders:
        order.restaurants = set()
        order.restaurant_distances_flag = True
        for order_item in order.order_items.all():

            product_restaurants = [
                restaurant_item.restaurant for restaurant_item in restaurant_menu_items
                if restaurant_item.product.id == order_item.product.id
            ]

            if not order.restaurants:
                order.restaurants = set(product_restaurants)
                continue
            order.restaurants &= set(product_restaurants)

        customer_coords = get_place_coords(order.address)
        if not customer_coords:
            order.restaurant_distances_flag = False
        else:
            for restaurant in order.restaurants:
                restaurant_coords = get_place_coords(
                    restaurant.address
                )
                restaurant.distance = round(
                    distance.distance(customer_coords, restaurant_coords).km, 2
                )

            order.restaurants = sorted(order.restaurants, key=lambda x: x.distance)
    return render(
        request,
        template_name='order_items.html',
        context={'order_items': orders, 'path': request.path}
    )
