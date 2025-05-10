from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Tour, Review, Rental, Guide, Booking, User
from .forms import TourForm, ReviewForm, UserProfileForm, CustomUserCreationForm
from django.db.models import Count, Avg, Q, F
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.db.models import Subquery

def index(request):
    # Популярные туры: по количеству отзывов (top 5)
    popular_tours = Tour.objects.annotate(num_reviews=Count('reviews')).order_by('-num_reviews', '-price')[:5]
    # Лучшие гиды: по рейтингу (top 5)
    best_guides = Guide.objects.order_by('-rating')[:5]
    # Последние бронирования (top 5)
    latest_bookings = Booking.objects.select_related('user', 'tour').order_by('-date')[:5]
    
    # Пример 1: Использование __ для доступа к полям связанной модели
    # Получаем туры с рейтингом отзывов выше 4
    highly_rated_tours = Tour.objects.filter(reviews__rating__gte=4).distinct()
    
    # Пример 2: Получаем пользователей, которые забронировали туры с ценой выше 5000
    users_with_expensive_bookings = User.objects.filter(bookings__tour__price__gt=5000).distinct()
    
    # Примеры использования exclude():
    
    # Пример 1: Короткие туры (исключаем туры длительностью более 3 часов)
    short_tours = Tour.objects.exclude(duration__gt=3)[:3]
    
    # Пример 2: Недорогие туры (исключаем туры дороже 5000)
    affordable_tours = Tour.objects.exclude(price__gt=5000)[:3]
    
    # Пример 3: Туры без отзывов (exclude + связанная модель)
    tours_without_reviews = Tour.objects.exclude(reviews__isnull=False)[:3]
    
    # Пример 4: Свободные гиды (exclude + связанная модель через ManyToMany)
    free_guides = Guide.objects.exclude(guide_tours__isnull=False)[:3]
    
    # Пример использования count() - простая статистика для главной страницы
    total_tours_count = Tour.objects.count()
    active_tours_count = Tour.objects.filter(is_active=True).count()
    total_guides_count = Guide.objects.count()
    total_reviews_count = Review.objects.count()
    
    return render(request, 'main/index.html', {
        'popular_tours': popular_tours,
        'best_guides': best_guides,
        'latest_bookings': latest_bookings,
        'highly_rated_tours': highly_rated_tours,
        'users_with_expensive_bookings': users_with_expensive_bookings,
        'short_tours': short_tours,
        'affordable_tours': affordable_tours,
        'tours_without_reviews': tours_without_reviews,
        'free_guides': free_guides,
        # Добавляем статистику для отображения на странице
        'total_tours_count': total_tours_count,
        'active_tours_count': active_tours_count,
        'total_guides_count': total_guides_count,
        'total_reviews_count': total_reviews_count,
    })

# Демонстрация select_related
# Выводит список аренд с оптимизацией запросов к user и bike

def rental_list(request):
    rentals = Rental.objects.select_related('user', 'bike').all()
    return render(request, 'main/rental_list.html', {'rentals': rentals})

# Демонстрация prefetch_related
# Выводит список туров и всех гидов для каждого тура

def tour_guides_list(request):
    tours = Tour.objects.prefetch_related('guides').all()
    return render(request, 'main/tour_guides_list.html', {'tours': tours})

# CRUD операции для маршрутов
class TourListView(ListView):
    model = Tour
    template_name = 'main/tour_list.html'
    context_object_name = 'tours'
    paginate_by = 6  # Количество туров на странице
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Получаем параметры фильтрации из GET-запроса
        location = self.request.GET.get('location')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        duration = self.request.GET.get('duration')
        search_query = self.request.GET.get('search')
        created_after = self.request.GET.get('created_after')
        created_before = self.request.GET.get('created_before')
        rating = self.request.GET.get('rating')
        exclude_duration = self.request.GET.get('exclude_duration')
        hide_expensive = self.request.GET.get('hide_expensive')
        exclude_location = self.request.GET.get('exclude_location')
        highly_rated = self.request.GET.get('highly_rated')
        
        # Применяем фильтры, если они указаны
        if location:
            # Пример использования __icontains (регистронезависимый поиск по подстроке)
            queryset = queryset.filter(location__icontains=location)
            
        if min_price:
            # Пример использования __gte (greater than or equal - больше или равно)
            queryset = queryset.filter(price__gte=min_price)
            
        if max_price:
            # Пример использования __lte (less than or equal - меньше или равно)
            queryset = queryset.filter(price__lte=max_price)
            
        if duration:
            # Пример использования точного сравнения (без __)
            queryset = queryset.filter(duration=duration)
            
        if search_query:
            # Пример использования __icontains с объединением условий через | (OR)
            queryset = queryset.filter(name__icontains=search_query) | queryset.filter(description__icontains=search_query)
        
        if created_after:
            # Пример использования __gte для даты
            queryset = queryset.filter(created_at__gte=created_after)
            
        if created_before:
            # Пример использования __lte для даты
            queryset = queryset.filter(created_at__lte=created_before)
            
        if rating:
            # Пример использования __ для связанной модели с агрегацией
            # Фильтруем туры со средним рейтингом выше указанного
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=rating)
        
        # Фильтрация только высоко оцененных туров
        if highly_rated:
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=4.5)
        
        # Пример использования __in (поиск в списке значений)
        # Фильтрация туров только с определенной длительностью (1, 2 или 4 часа)
        popular_durations = self.request.GET.getlist('popular_durations')
        if popular_durations:
            queryset = queryset.filter(duration__in=popular_durations)
            
        # Пример использования __startswith (начинается с)
        name_starts_with = self.request.GET.get('name_starts_with')
        if name_starts_with:
            queryset = queryset.filter(name__istartswith=name_starts_with)
            
        # Пример использования __range (в диапазоне)
        price_range = self.request.GET.getlist('price_range')
        if len(price_range) == 2:
            queryset = queryset.filter(price__range=(price_range[0], price_range[1]))
        
        # Примеры использования метода exclude()
        
        # 1. Исключаем туры с определенной длительностью
        if exclude_duration:
            queryset = queryset.exclude(duration=exclude_duration)
            
        # 2. Исключаем дорогие туры (цена > 10000)
        if hide_expensive:
            queryset = queryset.exclude(price__gt=10000)
        
        # 3. Исключаем туры из определенного местоположения
        if exclude_location:
            queryset = queryset.exclude(location__icontains=exclude_location)
        
        # 4. Исключаем туры без отзывов
        if self.request.GET.get('hide_without_reviews'):
            queryset = queryset.exclude(reviews=None)
            
        # 5. Исключаем недавно созданные туры (за последние 7 дней)
        if self.request.GET.get('hide_new'):
            week_ago = timezone.now() - timezone.timedelta(days=7)
            queryset = queryset.exclude(created_at__gte=week_ago)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем в контекст текущие параметры фильтрации для отображения в форме
        context['current_filters'] = {
            'location': self.request.GET.get('location', ''),
            'min_price': self.request.GET.get('min_price', ''),
            'max_price': self.request.GET.get('max_price', ''),
            'duration': self.request.GET.get('duration', ''),
            'search': self.request.GET.get('search', ''),
            'created_after': self.request.GET.get('created_after', ''),
            'created_before': self.request.GET.get('created_before', ''),
            'rating': self.request.GET.get('rating', ''),
            'popular_durations': self.request.GET.getlist('popular_durations', []),
            'name_starts_with': self.request.GET.get('name_starts_with', ''),
            'price_range': self.request.GET.getlist('price_range', []),
            'exclude_duration': self.request.GET.get('exclude_duration', ''),
            'hide_expensive': self.request.GET.get('hide_expensive', ''),
            'exclude_location': self.request.GET.get('exclude_location', ''),
            'hide_without_reviews': self.request.GET.get('hide_without_reviews', ''),
            'hide_new': self.request.GET.get('hide_new', ''),
            'highly_rated': self.request.GET.get('highly_rated', '')
        }
        # Добавляем список доступных вариантов длительности
        context['duration_choices'] = Tour.DURATION_CHOICES
        return context

class TourCreateView(CreateView):
    model = Tour
    form_class = TourForm
    template_name = 'main/tour_form.html'
    success_url = reverse_lazy('tour_list')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            # Получаем загруженный файл из request.FILES
            image = request.FILES.get('image')
            if image:
                # Создаем экземпляр модели с изображением
                tour = form.save(commit=False)
                tour.image = image
                tour.save()
            else:
                form.save()
            return redirect(self.success_url)
        return self.form_invalid(form)

class TourUpdateView(UpdateView):
    model = Tour
    form_class = TourForm
    template_name = 'main/tour_form.html'
    success_url = reverse_lazy('tour_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            # Получаем загруженный файл из request.FILES
            image = request.FILES.get('image')
            if image:
                # Обновляем изображение
                tour = form.save(commit=False)
                tour.image = image
                tour.save()
            else:
                form.save()
            return redirect(self.success_url)
        return self.form_invalid(form)

class TourDeleteView(DeleteView):
    model = Tour
    template_name = 'main/tour_confirm_delete.html'
    success_url = reverse_lazy('tour_list')

# Представление для создания отзыва
def create_review(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    
    # Пример использования exclude для получения других туров того же типа
    # Исключаем текущий тур и туры с меньшей длительностью
    similar_tours = Tour.objects.filter(duration=tour.duration).exclude(id=tour.id)[:3]
    
    # Пример exclude() - туры, на которые пользователь еще не оставил отзывы
    # useful если пользователь авторизован
    user_no_review_tours = []
    if request.user.is_authenticated:
        user_no_review_tours = Tour.objects.exclude(
            reviews__user=request.user
        ).exclude(id=tour.id)[:3]
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tour = tour
            review.user = request.user
            review.save()
            messages.success(request, 'Отзыв успешно добавлен!')
            return redirect('tour_list')
    else:
        form = ReviewForm()
    
    return render(request, 'main/review_form.html', {
        'form': form,
        'tour': tour,
        'similar_tours': similar_tours,
        'user_no_review_tours': user_no_review_tours
    })

@login_required
def profile(request):
    user = request.user
    
    # Стандартные запросы с использованием filter()
    user_bookings = Booking.objects.filter(user=user).select_related('tour')
    user_reviews = Review.objects.filter(user=user).select_related('tour')
    
    # Запросы с использованием exclude()
    
    # Пример 1: Не забронированные пользователем туры
    available_tours = Tour.objects.exclude(bookings__user=user)[:5]
    
    # Пример 2: Туры, на которые пользователь не оставлял отзывы
    tours_without_user_reviews = Tour.objects.exclude(reviews__user=user)[:5]
    
    # Пример 3: Последние туры, кроме слишком дорогих для пользователя
    affordable_new_tours = Tour.objects.order_by('-created_at').exclude(price__gt=5000)[:5]
    
    # Пример 4: Гиды без назначений на туры
    unassigned_guides = Guide.objects.exclude(guide_tours__isnull=False)[:3]
    
    # Примеры использования exists() - проверка наличия записей
    has_reviews = Review.objects.filter(user=user).exists()
    has_recent_bookings = Booking.objects.filter(
        user=user, 
        date__gte=timezone.now() - timezone.timedelta(days=30)
    ).exists()
    has_expensive_tours = user_bookings.filter(tour__price__gt=5000).exists()
    has_reviewed_all_tours = not Tour.objects.exclude(reviews__user=user).exists()
    
    return render(request, 'main/profile.html', {
        'user': user,
        'bookings': user_bookings,
        'reviews': user_reviews,
        'available_tours': available_tours,
        'tours_without_user_reviews': tours_without_user_reviews,
        'affordable_new_tours': affordable_new_tours,
        'unassigned_guides': unassigned_guides,
        # Добавляем результаты проверок exists()
        'has_reviews': has_reviews,
        'has_recent_bookings': has_recent_bookings,
        'has_expensive_tours': has_expensive_tours,
        'has_reviewed_all_tours': has_reviewed_all_tours,
    })

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'main/update_profile.html', {'form': form})
    
@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        logout(request)
        messages.success(request, 'Ваш аккаунт был успешно удален.')
        return redirect('index')
    return render(request, 'main/delete_account.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Вход пользователя сразу после регистрации
            messages.success(request, f'Добро пожаловать, {user.username}! Ваш аккаунт успешно создан.')
            return redirect('index')  # Перенаправление на главную страницу
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def exclude_examples(request):
    """Представление для демонстрации различных вариантов использования метода exclude()"""
    
    # 1. Базовый exclude с одним условием
    # Туры не из Москвы
    non_moscow_tours = Tour.objects.exclude(location__icontains='Москва')[:3]
    
    # 2. Exclude с несколькими условиями (цепочка вызовов)
    # Туры не из Москвы и не из Санкт-Петербурга
    non_msk_spb_tours = Tour.objects.exclude(location__icontains='Москва').exclude(location__icontains='Санкт-Петербург')[:3]
    
    # 3. Exclude с Q-объектами
    # Туры, которые не являются ни короткими (до 3 часов), ни дорогими (>5000)
    medium_tours = Tour.objects.exclude(
        Q(duration__lte=3) | Q(price__gt=5000)
    )[:3]
    
    # 4. Exclude для связанных моделей
    # Туры без отзывов с высоким рейтингом (>4)
    tours_without_high_ratings = Tour.objects.exclude(
        reviews__rating__gt=4
    ).distinct()[:3]
    
    # 5. Exclude с вложенными запросами (subqueries)
    # Туры, не забронированные в последний месяц
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_bookings = Booking.objects.filter(date__gte=thirty_days_ago)
    non_recent_booked_tours = Tour.objects.exclude(
        id__in=Subquery(recent_bookings.values('tour_id'))
    )[:3]
    
    # 6. Exclude с агрегацией
    from django.db.models import Count
    # Туры с менее чем 3 отзывами
    popular_tours = Tour.objects.annotate(
        review_count=Count('reviews')
    ).exclude(review_count__lt=3)[:3]
    
    # 7. Exclude с диапазоном дат
    # Туры, не созданные в последние 7 дней
    week_ago = timezone.now() - timezone.timedelta(days=7)
    older_tours = Tour.objects.exclude(created_at__gte=week_ago)[:3]
    
    return render(request, 'main/exclude_examples.html', {
        'non_moscow_tours': non_moscow_tours,
        'non_msk_spb_tours': non_msk_spb_tours,
        'medium_tours': medium_tours,
        'tours_without_high_ratings': tours_without_high_ratings,
        'non_recent_booked_tours': non_recent_booked_tours,
        'popular_tours': popular_tours,
        'older_tours': older_tours,
    })

# Пример использования count() и exists()
def count_exists_example(request):
    # Пример использования count() - подсчет количества
    total_tours = Tour.objects.count()
    active_tours_count = Tour.objects.filter(is_active=True).count()
    expensive_tours_count = Tour.objects.filter(price__gt=10000).count()
    
    # Пример использования exists() - проверка наличия
    has_premium_tours = Tour.objects.filter(price__gt=20000).exists()
    has_reviews = Review.objects.filter(user=request.user).exists() if request.user.is_authenticated else False
    has_recent_bookings = Booking.objects.filter(
        user=request.user, 
        date__gte=timezone.now() - timezone.timedelta(days=30)
    ).exists() if request.user.is_authenticated else False

    # Пример сравнения exists() и count() > 0
    # exists() эффективнее, когда нам просто нужно знать "есть" или "нет"
    
    return render(request, 'main/count_exists_example.html', {
        'total_tours': total_tours,
        'active_tours_count': active_tours_count,
        'expensive_tours_count': expensive_tours_count,
        'has_premium_tours': has_premium_tours,
        'has_reviews': has_reviews,
        'has_recent_bookings': has_recent_bookings,
    })

# Представление для детального просмотра тура
def tour_detail(request, tour_id):
    """Детальное представление тура с использованием методов модели для навигации"""
    tour = get_object_or_404(Tour, id=tour_id)
    
    # Получаем предыдущие и следующие туры относительно текущего
    next_tours = tour.get_next_tours(3)
    prev_tours = tour.get_prev_tours(3)
    
    # Получаем все отзывы для этого тура
    reviews = tour.reviews.select_related('user').order_by('-created_at')
    
    # Вычисляем средний рейтинг
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Похожие туры (с той же длительностью или из того же места)
    similar_tours = Tour.objects.filter(
        Q(duration=tour.duration) | Q(location__icontains=tour.location)
    ).exclude(id=tour.id)[:4]
    
    # Примеры использования exclude для рекомендаций
    # Туры с похожей ценой, но не с такой же длительностью
    price_range_min = float(tour.price) * 0.8
    price_range_max = float(tour.price) * 1.2
    price_similar_tours = Tour.objects.filter(
        price__range=(price_range_min, price_range_max)
    ).exclude(duration=tour.duration).distinct()[:3]
    
    return render(request, 'main/tour_detail.html', {
        'tour': tour,
        'next_tours': next_tours,
        'prev_tours': prev_tours,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'similar_tours': similar_tours,
        'price_similar_tours': price_similar_tours,
        'is_highly_rated': tour.is_highly_rated(),
    })

def bulk_tour_actions(request):
    """Представление для демонстрации массовых операций update() и delete()"""
    
    # Пример 1: Массовое обновление с update()
    # Деактивируем все туры старше 30 дней
    old_tours_count = Tour.objects.filter(
        created_at__lte=timezone.now() - timezone.timedelta(days=30)
    ).update(is_active=False)
    
    # Пример 2: Массовое обновление цен для коротких туров
    short_tours_updated = Tour.objects.filter(
        duration__lte=2
    ).update(price=F('price') * 0.9)  # Снижаем цену на 10%
    
    # Пример 3: Массовое удаление с delete()
    # Удаляем все неактивные туры без отзывов
    deleted_tours = Tour.objects.filter(
        is_active=False,
        reviews__isnull=True
    ).delete()
    
    # Пример 4: Обновление описания для туров в Москве
    moscow_tours_updated = Tour.objects.filter(
        location__icontains='Москва'
    ).update(description='Обновлено: Доступна новая система скидок для московских туров!')
    
    return render(request, 'main/bulk_actions_result.html', {
        'old_tours_count': old_tours_count,
        'short_tours_updated': short_tours_updated,
        'deleted_tours': deleted_tours[0] if isinstance(deleted_tours, tuple) else 0,  # Безопасное получение количества удаленных записей
        'moscow_tours_updated': moscow_tours_updated,
    }) 