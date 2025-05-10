# models.py (main/models.py)
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models import Avg

class User(AbstractUser):
    GENDER_CHOICES = (
        ('Мужской', 'Мужской'),
        ('Женский', 'Женский'),
    )
    ROLE_CHOICES = (
        ('Пользователь', 'Пользователь'),
        ('Гид', 'Гид'),
        ('Администратор', 'Администратор'),
    )

    # лаба 1: Демонстрация models.ImageField и Pillow
    # Поле для загрузки изображения пользователя
    # upload_to указывает подпапку в MEDIA_ROOT, куда будут сохраняться изображения
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='Аватар')
    
    gender = models.CharField(max_length=7, choices=GENDER_CHOICES, blank=True, null=True, verbose_name='Пол')
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Пользователь', verbose_name='Роль')

    # лаба 1: Демонстрация verbose_name и verbose_name_plural в Meta
    # verbose_name - отображаемое имя модели в единственном числе
    # verbose_name_plural - отображаемое имя модели во множественном числе
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.role})"

# лаба 1: Демонстрация использования сеансов Django
class Guide(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='guide_profile')
    experience = models.IntegerField(verbose_name='Опыт работы (лет)')
    languages = models.CharField(max_length=200, verbose_name='Знание языков')
    rating = models.FloatField(default=0.0, verbose_name='Рейтинг')
    # лаба 1: Демонстрация использования FileField
    resume = models.FileField(upload_to='guides/resumes/', verbose_name='Резюме', null=True, blank=True)
    # лаба 1: Демонстрация использования URLField
    profile_url = models.URLField(verbose_name='Ссылка на профиль', null=True, blank=True)
    # through: 
    tours = models.ManyToManyField('Tour', through='GuideTour', related_name='guides')

    class Meta:
        verbose_name = 'Гид'
        verbose_name_plural = 'Гиды'

    def __str__(self):
        return f"{self.user.username} - {self.experience} лет опыта"

    # лаба 1: Метод для отображения файла в админке
    def get_resume_url(self):
        if self.resume:
            return self.resume.url
        return None

# лаба 1: Демонстрация использования сеансов Django
class Location(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    address = models.TextField(verbose_name='Адрес')
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')

    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'

    def __str__(self):
        return self.name

# лаба 1: Демонстрация использования сеансов Django
class BikeStatus(models.Model):
    status_name = models.CharField(max_length=50, verbose_name='Название статуса')

    class Meta:
        verbose_name = 'Статус велосипеда'
        verbose_name_plural = 'Статусы велосипедов'

    def __str__(self):
        return self.status_name

# лаба 1: Демонстрация использования сеансов Django
class Bike(models.Model):
    BIKE_TYPES = [('standard', 'Обычный'), ('electric', 'Электрический')]
    type = models.CharField(max_length=20, choices=BIKE_TYPES, verbose_name='Тип')
    status = models.ForeignKey(BikeStatus, on_delete=models.CASCADE, verbose_name='Статус', related_name='bikes')
    rental_price_hour = models.FloatField(verbose_name='Цена за час')
    rental_price_day = models.FloatField(verbose_name='Цена за день')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name='Локация', related_name='bikes')

    class Meta:
        verbose_name = 'Велосипед'
        verbose_name_plural = 'Велосипеды'

    def __str__(self):
        return f"{self.get_type_display()} - {self.location.name}"

    def save(self, *args, **kwargs):
        if self.rental_price_hour < 0:  # Проверка цены
            self.rental_price_hour = 0
        super().save(*args, **kwargs)  # Важно!

# лаба 1: Демонстрация использования сеансов Django
class Rental(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='rentals')
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, verbose_name='Велосипед', related_name='rentals')
    start_time = models.DateTimeField(verbose_name='Время начала')
    end_time = models.DateTimeField(verbose_name='Время окончания')
    total_price = models.FloatField(verbose_name='Общая стоимость')

    class Meta:
        verbose_name = 'Аренда'
        verbose_name_plural = 'Аренды'

    def __str__(self):
        return f"{self.user.username} - {self.bike}"

# лаба 1: Демонстрация использования сеансов Django
class Tour(models.Model):
    # Варианты длительности тура
    DURATION_CHOICES = [
        (1, '1 час'),
        (2, '2 часа'),
        (3, '3 часа'),
        (4, '4 часа'),
        (6, '6 часов'),
        (8, '8 часов (целый день)'),
        (12, '12 часов'),
        (24, '24 часа (сутки)'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    duration = models.IntegerField(choices=DURATION_CHOICES, verbose_name='Длительность (часы)')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    location = models.CharField(max_length=200, verbose_name='Местоположение')
    image = models.ImageField(upload_to='tours/', verbose_name='Изображение', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    def __str__(self):
        # Получаем человекочитаемое значение для длительности
        duration_display = dict(self.DURATION_CHOICES).get(self.duration, f"{self.duration} ч.")
        return f"{self.name} ({duration_display})"

    def get_age(self):
        """Возвращает возраст тура в днях с момента создания"""
        if self.created_at:
            now = timezone.now()
            age = now - self.created_at
            return age.days
        return 0

    def was_recently_updated(self):
        """Проверяет, был ли тур обновлен за последний час"""
        now = timezone.now()
        return self.updated_at >= now - timezone.timedelta(hours=1)

    def is_highly_rated(self):
        """Проверяет, имеет ли тур высокий рейтинг (средний рейтинг >= 4.5)"""
        avg_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        # Если нет отзывов, возвращаем False
        if avg_rating is None:
            return False
        return avg_rating >= 4.5

    def get_next_tours(self, count=3):
        """Возвращает следующие туры по дате создания"""
        return Tour.objects.filter(created_at__gt=self.created_at).order_by('created_at')[:count]

    def get_prev_tours(self, count=3):
        """Возвращает предыдущие туры по дате создания"""
        return Tour.objects.filter(created_at__lt=self.created_at).order_by('-created_at')[:count]

    def save(self, *args, **kwargs):
        # Очищаем название от лишних пробелов
        self.name = self.name.strip()
        
        # Очищаем описание от лишних пробелов
        self.description = self.description.strip()
        
        # Очищаем местоположение от лишних пробелов
        self.location = self.location.strip()
        
        # Если это создание объекта (а не обновление)
        if not self.id:
            self.created_at = timezone.now()
        
        # В любом случае обновляем дату изменения
        self.updated_at = timezone.now()
        
        # Вызываем оригинальный метод save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'
        ordering = ['-created_at']

# лаба 1: Демонстрация использования сеансов Django
class GuideTour(models.Model):
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, verbose_name='Гид', related_name='guide_tours')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, verbose_name='Тур', related_name='guide_tours')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата назначения')

    class Meta:
        verbose_name = 'Назначение гида на тур'
        verbose_name_plural = 'Гиды и Туры'

    def __str__(self):
        return f"{self.guide} - {self.tour}"

# лаба 1: Демонстрация использования сеансов Django
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='bookings')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, verbose_name='Тур', related_name='bookings')
    date = models.DateTimeField(verbose_name='Дата')
    total_price = models.FloatField(verbose_name='Общая стоимость')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'

    def __str__(self):
        return f"{self.user.username} - {self.tour.name}"

# лаба 1: Демонстрация использования сеансов Django
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='reviews')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, verbose_name='Тур', related_name='reviews')
    rating = models.IntegerField(verbose_name='Оценка')
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"{self.user.username} - {self.tour.name} ({self.rating})"

# лаба 1: Демонстрация использования сеансов Django
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('completed', 'Завершен'),
        ('failed', 'Неудача'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='payments')
    amount = models.FloatField(verbose_name='Сумма')
    payment_method = models.CharField(max_length=50, verbose_name='Способ оплаты')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Статус')

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f"{self.user.username} - {self.amount} руб."

