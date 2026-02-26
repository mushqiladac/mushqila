from django.contrib import admin
from .models import Airport, FlightSearch


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ['iata_code', 'city', 'name', 'country', 'is_active']
    list_filter = ['country', 'is_active']
    search_fields = ['iata_code', 'icao_code', 'city', 'name', 'country']
    list_editable = ['is_active']


@admin.register(FlightSearch)
class FlightSearchAdmin(admin.ModelAdmin):
    list_display = ['origin', 'destination', 'departure_date', 'search_type', 'user', 'created_at']
    list_filter = ['search_type', 'cabin_class', 'created_at']
    search_fields = ['origin__iata_code', 'destination__iata_code', 'user__email']
    readonly_fields = ['created_at', 'search_hash']
    date_hierarchy = 'created_at'
