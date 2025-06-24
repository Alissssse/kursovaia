"""
Сериализаторы для bike tours: преобразование моделей в JSON и обратно.
"""
from rest_framework import serializers
from .models import Bike, Rental, User

class BikeSerializer(serializers.ModelSerializer):
    """Пример докстринга для сериализатора. Добавь аналогично ко всем классам и методам."""
    class Meta:
        model = Bike
        fields = '__all__'

class RentalSerializer(serializers.ModelSerializer):
    """Пример докстринга для сериализатора. Добавь аналогично ко всем классам и методам."""
    class Meta:
        model = Rental
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    """Пример докстринга для сериализатора. Добавь аналогично ко всем классам и методам."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role'] 