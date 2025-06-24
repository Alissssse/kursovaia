"""
Админка для bike tours: регистрация моделей, кастомизация отображения, фильтры.
"""
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import User, Guide, Tour, GuideTour, Rental, Bike, Location, Review, Booking, Slot
from django.utils.translation import gettext_lazy as _

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админка для пользователей."""
    list_display = ('username', 'email', 'role', 'gender', 'date_of_birth', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('role', 'gender')

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    """Админка для гидов."""
    list_display = ('user', 'experience', 'languages', 'rating')
    search_fields = ('user__username', 'languages')
    list_filter = ('experience',)

# Фильтр по наличию фото для Tour
class HasImageFilter(admin.SimpleListFilter):
    """Фильтр по наличию фото для Tour."""
    title = _('Наличие фото')
    parameter_name = 'has_image'

    def lookups(self, request, model_admin):
        """Опции фильтра: есть фото/нет фото."""
        return (
            ('yes', _('Есть фото')),
            ('no', _('Нет фото')),
        )

    def queryset(self, request, queryset):
        """Фильтрация queryset по наличию фото."""
        value = self.value()
        if value == 'yes':
            return queryset.exclude(image='')
        if value == 'no':
            return queryset.filter(image='')
        return queryset

class SlotInline(admin.TabularInline):
    """Инлайн-форма для слотов тура."""
    model = Slot
    extra = 1
    fields = ('guide', 'datetime', 'is_booked')
    autocomplete_fields = ['guide']
    show_change_link = True

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    """Админка для туров."""
    list_display = ('name', 'duration', 'price', 'location')
    search_fields = ('name', 'location')
    list_filter = ('location', HasImageFilter,)
    inlines = [SlotInline]
    
    class Media:
        """Подключение кастомных стилей и скриптов для админки тура."""
        css = {
            'all': ('css/custom_admin.css',)  # Путь относительно static/
        }
        js = (
            'js/price_validator.js',  # Путь относительно static/
            'js/duration_helper.js',
        )

@admin.register(GuideTour)
class GuideTourAdmin(admin.ModelAdmin):
    """Админка для связи гид-тур."""
    list_display = ('guide', 'tour', 'assigned_at')
    search_fields = ('guide__user__username', 'tour__name')
    list_filter = ('assigned_at',)

class BikeResource(resources.ModelResource):
    """Ресурс экспорта велосипедов."""
    def dehydrate_type(self, bike):
        """Преобразует тип велосипеда в строку для экспорта."""
        return bike.get_type_display() if hasattr(bike, 'get_type_display') else bike.type
    def get_export_queryset(self, request):
        """Фильтрует только доступные велосипеды для экспорта."""
        return super().get_export_queryset(request).filter(status__status_name='Доступен')
    def dehydrate_status(self, bike):
        """Преобразует статус велосипеда в строку для экспорта."""
        return bike.status.status_name if hasattr(bike.status, 'status_name') else str(bike.status)

class BikeAdmin(ImportExportModelAdmin):
    """Админка для велосипедов с экспортом."""
    resource_class = BikeResource
    list_display = ('id', 'type', 'status', 'location', 'rental_price_hour')
    list_filter = ('type', 'status', 'location')
    search_fields = ('type', 'location__name')
    readonly_fields = ('id',)
    list_display_links = ('id', 'type')
    fieldsets = (
        (None, {'fields': ('type', 'status', 'location')}),
        ('Цены', {'fields': ('rental_price_hour', 'rental_price_day')}),
    )

class RentalResource(resources.ModelResource):
    def get_export_queryset(self, request):
        return super().get_export_queryset(request).filter(end_time__isnull=False)

    def dehydrate_total_price(self, rental):
        return f"{rental.total_price} руб."

    def get_bike_display(self, rental):
        return f"{rental.bike.get_type_display()} ({rental.bike.location.name})"

    class Meta:
        model = Rental

class RentalAdmin(ImportExportModelAdmin):
    resource_class = RentalResource
    list_display = ('id', 'user', 'bike', 'start_time', 'end_time', 'total_price')
    list_filter = ('user', 'bike', 'start_time')
    search_fields = ('user__username', 'bike__type')
    readonly_fields = ('id',)
    list_display_links = ('id', 'user')
    fieldsets = (
        (None, {'fields': ('user', 'bike', 'start_time', 'end_time', 'total_price')}),
    )

# Удаляю старую регистрацию Rental, если есть
try:
    admin.site.unregister(Rental)
except admin.sites.NotRegistered:
    pass
admin.site.register(Rental, RentalAdmin)

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

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('tour', 'guide', 'datetime', 'is_booked')
    list_filter = ('tour', 'guide', 'is_booked')
    search_fields = ('tour__name', 'guide__user__username')

# ... existing code ...

# ... final translation line ...

# ... rest of the file ... 