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
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_place_coords(address):
    geocoder_key = settings.YANDEX_GEOCODER_API_KEY

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
