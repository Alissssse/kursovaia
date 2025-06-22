import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import Tour

class Command(BaseCommand):
    help = 'Updates the start_time for existing tours with random future dates.'

    def handle(self, *args, **kwargs):
        tours = Tour.objects.filter(start_time__isnull=True)
        now = timezone.now()
        updated_count = 0

        for tour in tours:
            # Generate a random future date within the next 30 days
            random_days = random.randint(1, 30)
            random_hour = random.randint(9, 18)
            random_minute = random.choice([0, 15, 30, 45])
            
            start_date = now + timedelta(days=random_days)
            start_time = start_date.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
            
            tour.start_time = start_time
            tour.save()
            updated_count += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully updated start_time for tour "{tour.name}" to {start_time}'))

        if updated_count == 0:
            self.stdout.write(self.style.WARNING('No tours needed updating. All tours already have a start_time.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Finished updating tour dates. Total tours updated: {updated_count}')) 