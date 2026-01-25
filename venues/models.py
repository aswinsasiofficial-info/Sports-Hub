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

class PricingRule(models.Model):
    PRICING_TYPE_CHOICES = (
        ('peak', 'Peak Hours'),
        ('off_peak', 'Off-Peak Hours'),
        ('weekend', 'Weekend Premium'),
        ('holiday', 'Holiday Premium'),
    )
    
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='pricing_rules')
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPE_CHOICES)
    start_time = models.TimeField(help_text="Start time for this pricing rule (e.g., 17:00)")
    end_time = models.TimeField(help_text="End time for this pricing rule (e.g., 21:00)")
    multiplier = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=1.00,
        help_text="Price multiplier (e.g., 1.5 = 50% increase, 0.8 = 20% discount)"
    )
    days_of_week = models.CharField(
        max_length=15, 
        blank=True,
        help_text="Comma-separated day numbers (0=Sunday, 1=Monday, etc.) or leave blank for all days"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        days = f" (Days: {self.days_of_week})" if self.days_of_week else ""
        return f"{self.get_pricing_type_display()}: {self.start_time}-{self.end_time} x{self.multiplier}{days}"
    
    def applies_to_day(self, day_of_week):
        """Check if this rule applies to a specific day of week (0=Sunday, 1=Monday, etc.)"""
        if not self.days_of_week:
            return True
        return str(day_of_week) in self.days_of_week.split(',')


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
    
    @property
    def calculated_price(self):
        """Calculate the price for this time slot based on pricing rules"""
        from datetime import datetime
        import calendar
        
        # Convert date to datetime for weekday calculation
        slot_datetime = datetime.combine(self.date, self.start_time)
        day_of_week = slot_datetime.weekday()  # Monday is 0, Sunday is 6
        # Convert to our system (Sunday=0, Monday=1, etc.)
        day_index = (day_of_week + 1) % 7
        
        # Get applicable pricing rules
        applicable_rules = []
        
        # Check all pricing rules for this venue
        for rule in self.venue.pricing_rules.filter(is_active=True):
            # Check if rule applies to this day
            if not rule.applies_to_day(day_index):
                continue
            
            # Check if time falls within rule period
            rule_start = rule.start_time
            rule_end = rule.end_time
            
            # Handle overnight rules (e.g., 22:00 to 06:00)
            if rule_end <= rule_start:  # Overnight rule
                if (self.start_time >= rule_start or self.start_time <= rule_end):
                    applicable_rules.append(rule)
            else:  # Regular rule
                if rule_start <= self.start_time <= rule_end:
                    applicable_rules.append(rule)
        
        # Apply the highest multiplier if multiple rules apply
        multiplier = 1.0
        if applicable_rules:
            multiplier = max(rule.multiplier for rule in applicable_rules)
        
        return round(float(self.venue.price_per_hour) * float(multiplier), 2)
    
    @property
    def pricing_info(self):
        """Get information about which pricing rules apply to this slot"""
        from datetime import datetime
        import calendar
        
        slot_datetime = datetime.combine(self.date, self.start_time)
        day_of_week = slot_datetime.weekday()
        day_index = (day_of_week + 1) % 7
        day_name = calendar.day_name[day_of_week]
        
        applicable_rules = []
        base_price = float(self.venue.price_per_hour)
        final_price = float(self.calculated_price)
        
        for rule in self.venue.pricing_rules.filter(is_active=True):
            if rule.applies_to_day(day_index):
                rule_start = rule.start_time
                rule_end = rule.end_time
                
                if rule_end <= rule_start:  # Overnight rule
                    if (self.start_time >= rule_start or self.start_time <= rule_end):
                        applicable_rules.append(rule)
                else:  # Regular rule
                    if rule_start <= self.start_time <= rule_end:
                        applicable_rules.append(rule)
        
        return {
            'day': day_name,
            'base_price': base_price,
            'final_price': final_price,
            'multiplier': final_price / base_price if base_price > 0 else 1.0,
            'rules_applied': applicable_rules,
            'is_peak': final_price > base_price,
            'is_discount': final_price < base_price
        }