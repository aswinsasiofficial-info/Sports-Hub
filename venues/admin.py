from django.contrib import admin
from .models import Sport, Venue, TimeSlot

@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport', 'owner', 'price_per_hour', 'is_active')
    list_filter = ('sport', 'is_active')
    search_fields = ('name', 'address')
    list_editable = ('is_active',)

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('venue', 'date', 'start_time', 'end_time', 'is_booked')
    list_filter = ('date', 'is_booked', 'venue__sport')
    search_fields = ('venue__name',)