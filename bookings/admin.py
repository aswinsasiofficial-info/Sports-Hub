from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'venue', 'booking_date', 'total_price', 'status')
    list_filter = ('status', 'booking_date', 'venue__sport')
    search_fields = ('user__username', 'venue__name')
    readonly_fields = ('booking_date',)