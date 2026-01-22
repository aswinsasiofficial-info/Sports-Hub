from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import razorpay
import json
from bookings.models import Booking

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def payment_success(request):
    order_id = request.GET.get('order_id')
    payment_id = request.GET.get('payment_id')
    signature = request.GET.get('signature')
    
    try:
        booking = Booking.objects.get(razorpay_order_id=order_id, user=request.user)
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        client.utility.verify_payment_signature(params_dict)
        
        # Update booking status
        booking.status = 'confirmed'
        booking.razorpay_payment_id = payment_id
        booking.razorpay_signature = signature
        booking.save()
        
        return render(request, 'payments/success.html', {'booking': booking})
        
    except Exception as e:
        return render(request, 'payments/error.html', {'error': str(e)})

@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        payload = request.body.decode('utf-8')
        signature = request.headers.get('X-Razorpay-Signature')
        
        try:
            client.utility.verify_webhook_signature(payload, signature, settings.RAZORPAY_WEBHOOK_SECRET)
            
            data = json.loads(payload)
            event = data['event']
            
            if event == 'payment.captured':
                payment_data = data['payload']['payment']['entity']
                order_id = payment_data['order_id']
                
                try:
                    booking = Booking.objects.get(razorpay_order_id=order_id)
                    booking.status = 'confirmed'
                    booking.razorpay_payment_id = payment_data['id']
                    booking.save()
                except Booking.DoesNotExist:
                    pass
                    
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error'})