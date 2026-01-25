from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from venues.models import Venue, TimeSlot
from .models import Booking
import razorpay
from django.conf import settings

@login_required
def create_booking(request):
    if request.method == 'POST':
        venue_id = request.POST.get('venue_id')
        time_slot_id = request.POST.get('time_slot_id')
        
        venue = get_object_or_404(Venue, id=venue_id, is_active=True)
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id, venue=venue, is_booked=False)
        
        # Calculate price (assuming 1-hour slots)
        total_price = venue.price_per_hour
        
        with transaction.atomic():
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                venue=venue,
                time_slot=time_slot,
                total_price=total_price,
                status='pending'
            )
            
            # Mark time slot as booked
            time_slot.is_booked = True
            time_slot.save()
            
            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            # Create Razorpay order
            razorpay_order = client.order.create({
                'amount': int(total_price * 100),  # Convert to paise
                'currency': 'INR',
                'payment_capture': '1'
            })
            
            booking.razorpay_order_id = razorpay_order['id']
            booking.save()
            
            context = {
                'booking': booking,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'amount': total_price,
            }
            
            return render(request, 'bookings/payment.html', context)
    
    return redirect('home')

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    
    # Calculate total spent on confirmed bookings
    confirmed_bookings = bookings.filter(status='confirmed')
    total_spent = sum(booking.total_price for booking in confirmed_bookings)
    
    context = {
        'bookings': bookings,
        'total_spent': total_spent,
    }
    
    return render(request, 'bookings/my_bookings.html', context)

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status in ['pending', 'confirmed']:
        booking.status = 'cancelled'
        booking.save()
        
        # Free up the time slot
        time_slot = booking.time_slot
        time_slot.is_booked = False
        time_slot.save()
        
        messages.success(request, 'Booking cancelled successfully')
    
    return redirect('my_bookings')