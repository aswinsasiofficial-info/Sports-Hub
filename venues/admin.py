from django.contrib import admin
from .models import Sport, Venue, TimeSlot, PricingRule

@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport', 'owner', 'price_per_hour', 'pricing_rules_count', 'is_active')
    list_filter = ('sport', 'is_active')
    search_fields = ('name', 'address')
    list_editable = ('is_active',)
    
    def pricing_rules_count(self, obj):
        count = obj.pricing_rules.filter(is_active=True).count()
        return f'{count} rules'
    pricing_rules_count.short_description = 'Active Pricing Rules'

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('venue', 'date', 'start_time', 'end_time', 'is_booked', 'calculated_price_display')
    list_filter = ('date', 'is_booked', 'venue__sport')
    search_fields = ('venue__name',)
    
    def calculated_price_display(self, obj):
        return f"₹{obj.calculated_price}"
    calculated_price_display.short_description = 'Price'

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('venue', 'pricing_type', 'start_time', 'end_time', 'multiplier', 'days_display', 'is_active')
    list_filter = ('pricing_type', 'is_active', 'venue__sport')
    search_fields = ('venue__name', 'pricing_type')
    list_editable = ('is_active',)
    
    def days_display(self, obj):
        if not obj.days_of_week:
            return 'All Days'
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        days = [day_names[int(d)] for d in obj.days_of_week.split(',') if d.isdigit()]
        return ', '.join(days)
    days_display.short_description = 'Days'