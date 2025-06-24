"""
Формы для bike tours: регистрация, бронирование, отзывы и т.д.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Tour, Review, User, Booking, Guide, GuideTour, Slot, Rental, BikeStatus, Bike

class TourForm(forms.ModelForm):
    """Форма для создания или обновления тура."""
    class Meta:
        model = Tour
        fields = ['name', 'description', 'price', 'duration', 'location', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'duration': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'})
        }

    def clean_duration(self):
        """Проверяет, что выбранная длительность является допустимой."""
        duration = self.cleaned_data.get('duration')
        valid_durations = [choice[0] for choice in Tour.DURATION_CHOICES]
        if duration not in valid_durations:
            raise forms.ValidationError("Выберите допустимую длительность из списка")
        return duration

    def clean_price(self):
        """Проверяет, что цена не отрицательная."""
        price = self.cleaned_data.get('price')
        if price < 0:
            raise forms.ValidationError("Цена не может быть отрицательной")
        return price

class ReviewForm(forms.ModelForm):
    """Форма для создания или обновления отзыва."""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'step': 1
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Напишите ваш отзыв...'
            })
        }

class UserProfileForm(forms.ModelForm):
    """Форма для обновления профиля пользователя."""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomUserCreationForm(UserCreationForm):
    """Форма для регистрации нового пользователя."""
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class BookingForm(forms.ModelForm):
    """Форма для бронирования тура."""
    slot = forms.ModelChoiceField(queryset=Slot.objects.none(), label='Доступные слоты', empty_label="Выберите слот", widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Booking
        fields = ['slot']

    def __init__(self, *args, **kwargs):
        tour = kwargs.pop('tour', None)
        super().__init__(*args, **kwargs)
        if tour:
            self.fields['slot'].queryset = Slot.objects.filter(tour=tour, is_booked=False).order_by('datetime')

class SlotForm(forms.ModelForm):
    """Форма для создания или обновления слота."""
    class Meta:
        model = Slot
        fields = ['guide', 'bike', 'datetime']
        widgets = {
            'guide': forms.Select(attrs={'class': 'form-control'}),
            'bike': forms.Select(attrs={'class': 'form-control'}),
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class RentalForm(forms.ModelForm):
    """Форма для создания или обновления аренды велосипеда."""
    class Meta:
        model = Rental
        fields = ['bike', 'start_time', 'end_time']
        widgets = {
            'bike': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показывать только доступные велосипеды
        available_status = BikeStatus.objects.filter(status_name='Доступен').first()
        if available_status:
            self.fields['bike'].queryset = Bike.objects.filter(status=available_status)
        else:
            self.fields['bike'].queryset = Bike.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        bike = cleaned_data.get('bike')
        if start_time and end_time and bike:
            duration_hours = (end_time - start_time).total_seconds() / 3600
            if duration_hours <= 0:
                raise forms.ValidationError('Время окончания должно быть позже времени начала.')
            # Если аренда больше 6 часов, считать как день
            if duration_hours > 6:
                cleaned_data['total_price'] = bike.rental_price_day
            else:
                cleaned_data['total_price'] = round(bike.rental_price_hour * duration_hours, 2)
        return cleaned_data 