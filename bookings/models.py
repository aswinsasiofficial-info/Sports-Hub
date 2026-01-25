from django.db import models
from accounts.models import User
from venues.models import Venue, TimeSlot

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'user'})
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Set total_price from time_slot's calculated price if not already set
        if not self.total_price and self.time_slot:
            self.total_price = self.time_slot.calculated_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} at {self.venue.name}"
    
    class Meta:
        ordering = ['-booking_date']