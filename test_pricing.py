from venues.models import Venue, TimeSlot, PricingRule
from datetime import date, time

# Test the pricing calculation
try:
    venue = Venue.objects.first()
    if venue:
        print(f'Testing pricing for venue: {venue.name}')
        print(f'Base price: ₹{venue.price_per_hour}')
        print()
        
        # Display all pricing rules
        print('Active Pricing Rules:')
        for rule in venue.pricing_rules.filter(is_active=True):
            print(f'  - {rule}')
        print()
        
        # Create test time slots
        test_cases = [
            (date(2026, 1, 25), time(10, 0), "Sunday morning"),
            (date(2026, 1, 26), time(10, 0), "Monday morning (Early Bird)"),
            (date(2026, 1, 26), time(18, 0), "Monday evening (Peak Hours)"),
            (date(2026, 1, 26), time(14, 0), "Monday afternoon (Regular)"),
        ]
        
        for test_date, test_time, description in test_cases:
            # Create time slot
            time_slot = TimeSlot.objects.create(
                venue=venue,
                date=test_date,
                start_time=test_time,
                end_time=time(test_time.hour + 1, test_time.minute)
            )
            
            pricing_info = time_slot.pricing_info
            print(f'{description}:')
            print(f'  Date: {test_date} {test_time}')
            print(f'  Day: {pricing_info["day"]}')
            print(f'  Base Price: ₹{pricing_info["base_price"]:.2f}')
            print(f'  Final Price: ₹{pricing_info["final_price"]:.2f}')
            print(f'  Multiplier: x{pricing_info["multiplier"]:.2f}')
            status = "PEAK" if pricing_info["is_peak"] else "DISCOUNT" if pricing_info["is_discount"] else "REGULAR"
            print(f'  Status: {status}')
            if pricing_info['rules_applied']:
                rules_str = ", ".join([rule.get_pricing_type_display() for rule in pricing_info["rules_applied"]])
                print(f'  Rules Applied: {rules_str}')
            print('-' * 50)
            
            # Clean up test time slot
            time_slot.delete()
    else:
        print('No venues found.')
except Exception as e:
    print(f'Error: {e}')