from django.contrib import admin
from .models import User, Guide, Tour, GuideTour, Rental, Bike, Location, Review, Booking

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'gender', 'date_of_birth', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('role', 'gender')

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience', 'languages', 'rating')
    search_fields = ('user__username', 'languages')
    list_filter = ('experience',)

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'location')
    search_fields = ('name', 'location')
    list_filter = ('location',)
    
    class Media:
        css = {
            'all': ('css/custom_admin.css',)  # Путь относительно static/
        }
        js = (
            'js/price_validator.js',  # Путь относительно static/
            'js/duration_helper.js',
        )

@admin.register(GuideTour)
class GuideTourAdmin(admin.ModelAdmin):
    list_display = ('guide', 'tour', 'assigned_at')
    search_fields = ('guide__user__username', 'tour__name')
    list_filter = ('assigned_at',)

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('user', 'bike', 'start_time', 'end_time', 'total_price')
    search_fields = ('user__username', 'bike__id')
    list_filter = ('start_time', 'end_time')

@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ('type', 'status', 'rental_price_hour', 'rental_price_day', 'location')
    search_fields = ('type', 'location__name')
    list_filter = ('type', 'status')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'latitude', 'longitude')
    search_fields = ('name', 'address')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'tour', 'rating', 'created_at')
    search_fields = ('user__username', 'tour__name')
    list_filter = ('rating', 'created_at')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'tour', 'date', 'total_price')
    search_fields = ('user__username', 'tour__name')
    list_filter = ('date',) 