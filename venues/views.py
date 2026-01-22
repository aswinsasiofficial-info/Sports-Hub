from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Venue, Sport, TimeSlot
from datetime import date, datetime

def home(request):
    sports = Sport.objects.all()
    featured_venues = Venue.objects.filter(is_active=True)[:6]
    
    context = {
        'sports': sports,
        'featured_venues': featured_venues,
    }
    return render(request, 'venues/home.html', context)

def venue_list(request):
    sport_filter = request.GET.get('sport', '')
    location_filter = request.GET.get('location', '')
    
    venues = Venue.objects.filter(is_active=True)
    
    if sport_filter:
        venues = venues.filter(sport__name=sport_filter)
    
    if location_filter:
        venues = venues.filter(
            Q(address__icontains=location_filter) | 
            Q(location__icontains=location_filter)
        )
    
    sports = Sport.objects.all()
    
    context = {
        'venues': venues,
        'sports': sports,
        'selected_sport': sport_filter,
    }
    return render(request, 'venues/venue_list.html', context)

def venue_detail(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id, is_active=True)
    
    # Get available time slots
    today = date.today()
    time_slots = TimeSlot.objects.filter(
        venue=venue,
        date__gte=today,
        is_booked=False
    ).order_by('date', 'start_time')
    
    context = {
        'venue': venue,
        'time_slots': time_slots,
    }
    return render(request, 'venues/venue_detail.html', context)

def sport_venues(request, sport_name):
    sport = get_object_or_404(Sport, name=sport_name)
    venues = Venue.objects.filter(sport=sport, is_active=True)
    
    context = {
        'sport': sport,
        'venues': venues,
    }
    return render(request, 'venues/sport_venues.html', context)