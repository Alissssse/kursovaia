# populate_db.py
import os
import random
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, is_aware
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from main.models import *
from django.contrib.auth.hashers import make_password

FIRST_NAMES_MALE = ['Александр', 'Дмитрий', 'Максим', 'Сергей', 'Андрей', 'Алексей', 'Иван', 'Артем', 'Николай', 'Михаил']
FIRST_NAMES_FEMALE = ['Елена', 'Ольга', 'Наталья', 'Анна', 'Мария', 'Ирина', 'Светлана', 'Татьяна', 'Екатерина', 'Юлия']
LAST_NAMES = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Павлов', 'Семенов', 'Голубев']
LANGUAGES = ['Русский', 'Английский', 'Французский', 'Немецкий', 'Испанский', 'Китайский', 'Японский']
EXPERIENCES = [
    "Опытный гид с 10-летним стажем",
    "Профессиональный гид с лицензией",
    "Любитель истории с большим опытом экскурсий",
    "Гид-энтузиаст, знаток местных достопримечательностей",
    "Лицензированный гид-переводчик"
]
LOCATIONS = [
    ("Центральный парк", "ул. Центральная, 1", 55.751244, 37.618423),
    ("Набережная реки", "ул. Набережная, 5", 55.753933, 37.620792),
    ("Исторический центр", "пл. Историческая, 3", 55.758631, 37.619844),
    ("Горный район", "ул. Горная, 12", 55.763511, 37.625678),
    ("Озеро", "ул. Озерная, 7", 55.766422, 37.615432)
]
TOUR_NAMES = [
    "Историческая экскурсия",
    "Гастрономический тур",
    "Велосипедная прогулка",
    "Ночная экскурсия",
    "Экскурсия для детей",
    "Архитектурный тур",
    "Литературный маршрут"
]
TOUR_DESCRIPTIONS = [
    "Увлекательное путешествие по историческим местам города",
    "Знакомство с местной кухней и традициями",
    "Активный отдых с осмотром достопримечательностей",
    "Необычный взгляд на город в ночных огнях",
    "Специальная программа для маленьких путешественников",
    "Исследование архитектурных стилей и памятников",
    "Маршрут по местам, связанным с известными писателями"
]
BIKE_STATUSES = ['Доступен', 'В аренде', 'На обслуживании', 'Сломан']
PAYMENT_METHODS = ['Карта', 'Наличные', 'Онлайн-перевод', 'Криптовалюта']
COMMENTS = [
    "Отличный тур, всем рекомендую!",
    "Гид был очень знающий и дружелюбный.",
    "Немного устали, но впечатления прекрасные.",
    "Не все было организовано идеально, но в целом понравилось.",
    "Прекрасный способ познакомиться с городом!",
    "Ожидали большего за такую цену.",
    "Обязательно вернемся и возьмем еще один тур!"
]

def create_users(num=20):
    """Создание случайных пользователей"""
    for i in range(num):
        gender = random.choice(['Мужской', 'Женский'])
        if gender == 'Мужской':
            first_name = random.choice(FIRST_NAMES_MALE)
        else:
            first_name = random.choice(FIRST_NAMES_FEMALE)
        
        last_name = random.choice(LAST_NAMES)
        username = f"{first_name.lower()}_{last_name.lower()}_{i}"
        email = f"{username}@example.com"
        

        rand = random.random()
        if rand < 0.02:
            role = 'Администратор'
        elif rand < 0.1:
            role = 'Гид'
        else:
            role = 'Пользователь'
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=datetime.now() - timedelta(days=random.randint(18*365, 70*365)),
            role=role,
            password=make_password('password123')
        )
   
        if role == 'Гид':
            Guide.objects.create(
                user=user,
                experience=random.randint(1, 20),
                resume=random.choice(EXPERIENCES),
                languages=', '.join(random.sample(LANGUAGES, random.randint(1, 3))),
                rating=round(random.uniform(3.5, 5.0), 1)
            )

def create_locations():
    """Создание локаций"""
    for name, address, lat, lng in LOCATIONS:
        Location.objects.create(
            name=name,
            address=address,
            latitude=lat,
            longitude=lng
        )

def create_bike_statuses():
    """Создание статусов велосипедов"""
    for status in BIKE_STATUSES:
        BikeStatus.objects.create(status_name=status)

def create_bikes(num=30):
    """Создание велосипедов"""
    statuses = list(BikeStatus.objects.all())
    locations = list(Location.objects.all())
    
    for i in range(num):
        bike_type = random.choice(['standard', 'electric'])
        if bike_type == 'standard':
            price_hour = round(random.uniform(5, 15), 2)
            price_day = round(random.uniform(30, 70), 2)
        else:
            price_hour = round(random.uniform(10, 25), 2)
            price_day = round(random.uniform(50, 100), 2)
        
        Bike.objects.create(
            type=bike_type,
            status=random.choice(statuses),
            rental_price_hour=price_hour,
            rental_price_day=price_day,
            location=random.choice(locations)
        )

def create_tours(num=15):
    """Создание туров"""
    locations = list(Location.objects.all())
    
    for i in range(num):
        duration = random.choice([1, 2, 3, 4, 6, 8])
        loc = random.choice(locations)
        Tour.objects.create(
            name=f"{random.choice(TOUR_NAMES)} {i+1}",
            description=random.choice(TOUR_DESCRIPTIONS),
            duration=duration,
            price=round(duration * random.uniform(10, 25), 2),
            location=loc.name
        )

def assign_guides_to_tours():
    """Назначение гидов на туры"""
    guides = list(Guide.objects.all())
    tours = list(Tour.objects.all())
    
    for tour in tours:
       
        for _ in range(random.randint(1, 3)):
            GuideTour.objects.create(
                guide=random.choice(guides),
                tour=tour,
                assigned_at=make_aware(datetime.now() - timedelta(days=random.randint(1, 365)))
            )

def create_rentals(num=50):
    """Создание записей об аренде"""
    users = list(User.objects.filter(role='Пользователь'))
    bikes = list(Bike.objects.filter(status__status_name='Доступен'))
    
    for _ in range(num):
        user = random.choice(users)
        bike = random.choice(bikes)
        start_time = make_aware(datetime.now() - timedelta(days=random.randint(1, 30)))
        end_time = start_time + timedelta(hours=random.randint(1, 24))

        duration_hours = (end_time - start_time).total_seconds() / 3600
        if duration_hours > 6:  
            total_price = bike.rental_price_day
        else:
            total_price = round(bike.rental_price_hour * duration_hours, 2)
        
        Rental.objects.create(
            user=user,
            bike=bike,
            start_time=start_time,
            end_time=end_time,
            total_price=total_price
        )

def create_bookings(num=40):
    """Создание бронирований туров"""
    users = list(User.objects.all())
    tours = list(Tour.objects.all())
    
    for _ in range(num):
        user = random.choice(users)
        tour = random.choice(tours)
        date = make_aware(datetime.now() + timedelta(days=random.randint(1, 60)))
        
        Booking.objects.create(
            user=user,
            tour=tour,
            date=date,
            total_price=tour.price
        )

def create_reviews(num=30):
    """Создание отзывов"""
    users = list(User.objects.filter(role='Пользователь'))
    bookings = list(Booking.objects.all())
    for _ in range(num):
        booking = random.choice(bookings)
        user = booking.user
        tour = booking.tour
        rating = random.randint(3, 5)
        comment = random.choice(COMMENTS)
        created_at = booking.date + timedelta(days=random.randint(1, 7))
        if not is_aware(created_at):
            created_at = make_aware(created_at)
        Review.objects.create(
            user=user,
            tour=tour,
            rating=rating,
            comment=comment,
            created_at=created_at
        )

def create_payments(num=60):
    """Создание платежей"""
    users = list(User.objects.all())
    rentals = list(Rental.objects.all())
    bookings = list(Booking.objects.all())
    
    for _ in range(num):
        user = random.choice(users)
        amount = round(random.uniform(10, 500), 2)
        status = random.choices(
            ['pending', 'completed', 'failed'],
            weights=[0.1, 0.85, 0.05]
        )[0]
        
       
        related_obj = None
        if random.random() > 0.3:
            if random.random() > 0.5 and rentals:
                related_obj = random.choice(rentals)
                amount = related_obj.total_price
            elif bookings:
                related_obj = random.choice(bookings)
                amount = related_obj.total_price
        
        Payment.objects.create(
            user=user,
            amount=amount,
            payment_method=random.choice(PAYMENT_METHODS),
            status=status
        )

def main():
    print("Начало заполнения базы данных...")
    

    
    create_users()
    print("Пользователи созданы")
    
    create_locations()
    print("Локации созданы")
    
    create_bike_statuses()
    print("Статусы велосипедов созданы")
    
    create_bikes()
    print("Велосипеды созданы")
    
    create_tours()
    print("Туры созданы")
    
    assign_guides_to_tours()
    print("Гиды назначены на туры")
    
    create_rentals()
    print("Аренды созданы")
    
    create_bookings()
    print("Бронирования созданы")
    
    create_reviews()
    print("Отзывы созданы")
    
    create_payments()
    print("Платежи созданы")
    
    print("Заполнение базы данных завершено!")

if __name__ == "__main__":
    main()