from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import User
from venues.models import Venue
from bookings.models import Booking

# Authentication Views
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        user_type = request.POST.get('user_type', 'user')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('signup')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            user_type=user_type
        )
        
        login(request, user)
        messages.success(request, 'Account created successfully!')
        
        if user_type == 'owner':
            return redirect('owner_dashboard')
        return redirect('home')
    
    return render(request, 'accounts/signup.html')

def owner_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.user_type == 'owner':
            login(request, user)
            return redirect('owner_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an owner')
    
    return render(request, 'accounts/owner_login.html')

@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == "GET":
        # Show confirmation page
        return render(request, 'accounts/logout.html')
    elif request.method == "POST":
        # Perform logout
        logout(request)
        messages.success(request, 'You have been successfully logged out!')
        return redirect('home')
    return redirect('home')

# Profile Views
@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

def is_owner(user):
    return user.user_type == 'owner'

@login_required
@user_passes_test(is_owner)
def owner_dashboard(request):
    # Get owner's venues
    venues = Venue.objects.filter(owner=request.user)
    
    # Get bookings for owner's venues
    venue_ids = venues.values_list('id', flat=True)
    bookings = Booking.objects.filter(venue_id__in=venue_ids).order_by('-booking_date')
    
    # Calculate total revenue
    total_revenue = 0
    for booking in bookings:
        total_revenue += booking.total_price
    
    # Calculate daily orders
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    last_week = today - timedelta(days=7)
    
    daily_orders = Booking.objects.filter(
        venue_id__in=venue_ids,
        booking_date__date__gte=last_week
    ).values('booking_date__date').annotate(
        count=Count('id'),
        daily_revenue=Sum('total_price')
    ).order_by('booking_date__date')
    
    # Calculate monthly revenue
    monthly_revenue = Booking.objects.filter(
        venue_id__in=venue_ids,
        booking_date__month=datetime.now().month,
        booking_date__year=datetime.now().year
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    context = {
        'venues': venues,
        'bookings': bookings,
        'daily_orders': daily_orders,
        'total_venues': venues.count(),
        'total_bookings': bookings.count(),
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
    }
    
    return render(request, 'accounts/owner_dashboard.html', context)