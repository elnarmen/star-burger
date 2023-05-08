import requests
from django.utils import timezone
from django.shortcuts import render
from django.conf import settings
from placesapp.models import Place


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()

    try:
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    except (KeyError, ValueError):
        return None

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


def save_place(address):
    place, _ = Place.objects.get_or_create(address=address)
    try:
        place_coords = fetch_coordinates(
            settings.YANDEX_GEOCODER_API_KEY,
            address
        )
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException):
        place.latitude = place.longitude = None
        place.update_time = timezone.now()
        place.save()
        return

    if not place_coords:
        place.latitude = place.longitude = None
        place.update_time = timezone.now()
        place.save()
        return

    place.latitude, place.longitude = place_coords
    place.save()

