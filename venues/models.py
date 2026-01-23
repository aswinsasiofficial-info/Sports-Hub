from django.db import models
from accounts.models import User
import os

def venue_image_path(instance, filename):
    return f'venues/{instance.id}/{filename}'

class Sport(models.Model):
    SPORT_CHOICES = (
        ('badminton', 'Badminton'),
        ('cricket', 'Cricket'),
        ('football', 'Football'),
        ('tennis', 'Tennis'),
        ('swimming', 'Swimming'),
        ('boxing', 'Boxing'),
    )
    
    name = models.CharField(max_length=20, choices=SPORT_CHOICES, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(max_length=50, blank=True)
    
    def __str__(self):
        return self.get_name_display()

class Venue(models.Model):
    name = models.CharField(max_length=200)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'owner'})
    image = models.ImageField(upload_to=venue_image_path)
    address = models.TextField()
    location = models.CharField(max_length=200)  # Could be Google Maps link or coordinates
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sport})"
    
    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return '/static/images/default-venue.jpg'

class TimeSlot(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='timeslots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('venue', 'date', 'start_time', 'end_time')
    
    def __str__(self):
        return f"{self.venue.name} - {self.date} {self.start_time} to {self.end_time}"