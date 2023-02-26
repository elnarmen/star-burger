from django.contrib import admin
from placesapp.models import Place

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    pass
