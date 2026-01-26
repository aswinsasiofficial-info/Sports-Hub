from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from io import BytesIO
from .models import User
from .forms import UserProfileForm, ChangePasswordForm, DeleteAccountForm
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
    """User profile page"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()  # This saves the data to database
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Calculate user statistics
    from bookings.models import Booking
    from venues.models import Venue
    
    # User stats
    user_bookings = Booking.objects.filter(user=request.user)
    total_spent = sum(booking.total_price for booking in user_bookings if booking.status == 'confirmed')
    total_bookings = user_bookings.count()
    
    # Owner stats (if user is owner)
    owned_venues = 0
    total_revenue = 0
    if request.user.user_type == 'owner':
        owned_venues = Venue.objects.filter(owner=request.user).count()
        owner_bookings = Booking.objects.filter(venue__owner=request.user)
        total_revenue = sum(booking.total_price for booking in owner_bookings if booking.status == 'confirmed')
    
    context = {
        'form': form,
        'total_spent': total_spent,
        'total_bookings': total_bookings,
        'owned_venues': owned_venues,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def download_invoice(request, booking_id):
    """Generate and download PDF invoice for a booking"""
    try:
        from bookings.models import Booking
        from django.template.loader import get_template
        from datetime import datetime
        
        # Get booking and verify ownership
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Users can only download their own invoices, owners can download invoices for their venues
        if request.user != booking.user and not (request.user.user_type == 'owner' and booking.venue.owner == request.user):
            messages.error(request, 'You do not have permission to access this invoice.')
            return redirect('profile')
        
        # Calculate tax (18% GST)
        tax_rate = 0.18
        tax_amount = float(booking.total_price) * tax_rate
        total_with_tax = float(booking.total_price) + tax_amount
        
        # Prepare context
        context = {
            'booking': booking,
            'tax_amount': tax_amount,
            'total_with_tax': total_with_tax,
            'current_date': datetime.now(),
        }
        
        # Try to generate PDF if xhtml2pdf is available
        try:
            from xhtml2pdf import pisa
            
            # Render HTML template
            template = get_template('accounts/invoice.html')
            html = template.render(context)
            
            # Create PDF
            result = BytesIO()
            pdf = pisa.CreatePDF(html, dest=result)
            
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename=invoice_{booking.id}.pdf'
                return response
            else:
                # If PDF generation fails, return an error page
                messages.error(request, 'Error generating PDF invoice. Please try again.')
                return redirect('profile')
        except ImportError:
            # If xhtml2pdf is not available, generate a simple HTML invoice
            template = get_template('accounts/invoice.html')
            html = template.render(context)
            return HttpResponse(html, content_type='text/html')
            
    except Exception as e:
        messages.error(request, f'Error generating invoice: {str(e)}')
        return redirect('profile')

@login_required
def delete_account(request):
    """Delete user account with confirmation"""
    if request.method == 'POST':
        form = DeleteAccountForm(request.user, request.POST)
        if form.is_valid():
            # Delete all related data first
            from bookings.models import Booking
            from venues.models import Venue
            
            # Delete user's bookings
            Booking.objects.filter(user=request.user).delete()
            
            # If user is an owner, delete their venues
            if request.user.user_type == 'owner':
                Venue.objects.filter(owner=request.user).delete()
            
            # Delete the user account
            username = request.user.username
            request.user.delete()
            
            messages.success(request, f'Account {username} has been permanently deleted.')
            return redirect('home')
    else:
        form = DeleteAccountForm(request.user)
    
    return render(request, 'accounts/delete_account.html', {'form': form})

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ChangePasswordForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})

def is_owner(user):
    return user.user_type == 'owner'

@login_required
@user_passes_test(is_owner)
def owner_dashboard(request):
    if request.method == 'POST':
        # Handle venue creation
        from venues.models import Sport
        
        name = request.POST.get('name')
        sport_name = request.POST.get('sport')
        price = request.POST.get('price')
        address = request.POST.get('address')
        location = request.POST.get('location', '')
        image = request.FILES.get('image')
        
        # Validate required fields
        if not all([name, sport_name, price, address]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('owner_dashboard')
        
        try:
            # Get the sport object
            sport = Sport.objects.get(name=sport_name)
            
            # Create the venue
            venue = Venue.objects.create(
                name=name,
                sport=sport,
                owner=request.user,
                address=address,
                location=location,
                price_per_hour=price,
                image=image if image else None
            )
            
            messages.success(request, f'Venue "{venue.name}" has been added successfully!')
            return redirect('owner_venues')  # Redirect to venues page after creation
            
        except Sport.DoesNotExist:
            messages.error(request, 'Invalid sport selected.')
            return redirect('owner_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating venue: {str(e)}')
            return redirect('owner_dashboard')
    
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

@login_required
@user_passes_test(is_owner)
def owner_venues(request):
    """Display all venues owned by the current user"""
    if request.method == 'POST':
        # Handle venue creation
        from venues.models import Sport
        
        name = request.POST.get('name')
        sport_name = request.POST.get('sport')
        price = request.POST.get('price')
        address = request.POST.get('address')
        location = request.POST.get('location', '')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate required fields
        if not all([name, sport_name, price, address]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('owner_venues')
        
        try:
            # Get the sport object
            sport = Sport.objects.get(name=sport_name)
            
            # Create the venue
            venue = Venue.objects.create(
                name=name,
                sport=sport,
                owner=request.user,
                address=address,
                location=location,
                price_per_hour=price,
                image=image if image else None,
                is_active=is_active
            )
            
            messages.success(request, f'Venue "{venue.name}" has been added successfully!')
            return redirect('owner_venues')  # Stay on the same page after creation
            
        except Sport.DoesNotExist:
            messages.error(request, 'Invalid sport selected.')
            return redirect('owner_venues')
        except Exception as e:
            messages.error(request, f'Error creating venue: {str(e)}')
            return redirect('owner_venues')
    
    venues = Venue.objects.filter(owner=request.user).order_by('-created_at')
    
    # Calculate venue statistics
    total_venues = venues.count()
    active_venues = venues.filter(is_active=True).count()
    inactive_venues = venues.filter(is_active=False).count()
    
    # Calculate total bookings and revenue for all venues
    from django.db.models import Sum
    from bookings.models import Booking
    
    venue_ids = venues.values_list('id', flat=True)
    total_bookings = Booking.objects.filter(venue_id__in=venue_ids).count()
    total_revenue = Booking.objects.filter(
        venue_id__in=venue_ids, 
        status='confirmed'
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    context = {
        'venues': venues,
        'total_venues': total_venues,
        'active_venues': active_venues,
        'inactive_venues': inactive_venues,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'accounts/owner_venues.html', context)

@login_required
@user_passes_test(is_owner)
def owner_bookings(request):
    """Display all bookings for owner's venues"""
    # Get owner's venues
    venues = Venue.objects.filter(owner=request.user)
    venue_ids = venues.values_list('id', flat=True)
    
    # Get bookings for all owner's venues
    bookings = Booking.objects.filter(venue_id__in=venue_ids).order_by('-booking_date')
    
    # Calculate statistics
    from django.db.models import Sum, Count
    
    total_bookings = bookings.count()
    confirmed_bookings = bookings.filter(status='confirmed')
    pending_bookings = bookings.filter(status='pending')
    cancelled_bookings = bookings.filter(status='cancelled')
    
    total_revenue = confirmed_bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Group by status
    booking_stats = bookings.values('status').annotate(count=Count('id'))
    
    # Recent bookings (last 10)
    recent_bookings = bookings[:10]
    
    context = {
        'bookings': bookings,
        'recent_bookings': recent_bookings,
        'total_bookings': total_bookings,
        'confirmed_count': confirmed_bookings.count(),
        'pending_count': pending_bookings.count(),
        'cancelled_count': cancelled_bookings.count(),
        'total_revenue': total_revenue,
        'venues': venues,
        'booking_stats': booking_stats,
    }
    
    return render(request, 'accounts/owner_bookings.html', context)