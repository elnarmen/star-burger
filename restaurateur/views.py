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
from placesapp.location_utils import fetch_coordinates, save_place

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


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects\
        .annotate(total_cost=Sum('items__total_price'))\
        .exclude(status='D')\
        .prefetch_related('cooking_restaurant', 'items', 'items__product')\
        .order_by('status')

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

            product_restaurants = [
                rest_item.restaurant for rest_item in restaurant_menu_items
                if rest_item.availability and rest_item.product.id == order_item.product.id
            ]

            if not order.restaurants:
                order.restaurants = set(product_restaurants)
                continue
            order.restaurants &= set(product_restaurants)

        order_place = places.get(order.address)
        order_coords = order_place.latitude, order_place.latitude
        if None in order_coords:
            order.restaurant_distances_flag = False
        else:
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
    return render(
        request,
        template_name='order_items.html',
        context={'order_items': orders, 'path': request.path}
    )
