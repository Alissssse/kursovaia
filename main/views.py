"""
Вьюхи для bike tours: отображение туров, бронирований, профилей и т.д.
"""

import datetime
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Avg, Q, F
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.db.models import Subquery
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator

from .models import Tour, Review, Rental, Guide, Booking, User, create_manager_group, Bike, Slot
from .forms import TourForm, ReviewForm, UserProfileForm, CustomUserCreationForm, BookingForm, SlotForm, RentalForm
from .serializers import BikeSerializer, RentalSerializer, UserSerializer

class ManagerRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки прав менеджера или суперпользователя"""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Managers').exists()

    def handle_no_permission(self):
        raise PermissionDenied("У вас нет прав для выполнения этого действия")

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
    user_search = request.GET.get('user_search', '').strip()
    bike_search = request.GET.get('bike_search', '').strip()

    # Фильтрация по пользователю
    if not request.user.is_superuser and getattr(request.user, 'role', None) != 'Менеджер':
        rentals = rentals.filter(user=request.user)

    if user_search:
        rentals = rentals.filter(user__username__icontains=user_search)
    if bike_search:
        words = bike_search.lower().split()
        q = Q()
        for word in words:
            q &= (Q(bike__type__icontains=word) | Q(bike__location__name__icontains=word))
        if bike_search.isdigit():
            q |= Q(bike__id=int(bike_search))
        rentals_qs = rentals.filter(q)
        if rentals_qs.exists():
            rentals = rentals_qs
        else:
            rentals = [r for r in rentals if bike_search.lower() in str(r.bike).lower()]

    # Пагинация
    paginator = Paginator(rentals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'main/rental_list.html', {'page_obj': page_obj})

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
    paginate_by = 9

    def get_queryset(self):
        queryset = Tour.objects.all()
        
        # Получаем все параметры фильтрации
        search = self.request.GET.get('search', '')
        location = self.request.GET.get('location', '')
        min_price = self.request.GET.get('min_price', '')
        max_price = self.request.GET.get('max_price', '')
        duration = self.request.GET.get('duration', '')
        created_after = self.request.GET.get('created_after', '')
        created_before = self.request.GET.get('created_before', '')
        rating = self.request.GET.get('rating', '')
        name_starts_with = self.request.GET.get('name_starts_with', '')
        popular_durations = self.request.GET.getlist('popular_durations', [])
        hide_expensive = self.request.GET.get('hide_expensive', '')
        hide_without_reviews = self.request.GET.get('hide_without_reviews', '')
        hide_new = self.request.GET.get('hide_new', '')
        highly_rated = self.request.GET.get('highly_rated', '')
        exclude_duration = self.request.GET.get('exclude_duration', '')
        exclude_location = self.request.GET.get('exclude_location', '')
        has_guide = self.request.GET.get('has_guide', '')

        # Применяем фильтры
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
            )
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        if duration:
            queryset = queryset.filter(duration=duration)
        
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        
        if rating:
            queryset = queryset.filter(rating__gte=rating)
        
        if name_starts_with:
            queryset = queryset.filter(name__istartswith=name_starts_with)
        
        if popular_durations:
            queryset = queryset.filter(duration__in=popular_durations)
        
        if hide_expensive:
            queryset = queryset.filter(price__lte=10000)
        
        if hide_without_reviews:
            queryset = queryset.exclude(reviews__isnull=True)
        
        if hide_new:
            seven_days_ago = timezone.now() - timezone.timedelta(days=7)
            queryset = queryset.exclude(created_at__gte=seven_days_ago)
        
        if highly_rated:
            queryset = queryset.filter(rating__gte=4.5)
        
        if exclude_duration:
            queryset = queryset.exclude(duration=exclude_duration)
        
        if exclude_location:
            queryset = queryset.exclude(location__icontains=exclude_location)
        
        if has_guide == '1':
            queryset = queryset.filter(guides__isnull=False)
        elif has_guide == '0':
            queryset = queryset.filter(guides__isnull=True)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем все текущие фильтры в контекст
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'location': self.request.GET.get('location', ''),
            'min_price': self.request.GET.get('min_price', ''),
            'max_price': self.request.GET.get('max_price', ''),
            'duration': self.request.GET.get('duration', ''),
            'created_after': self.request.GET.get('created_after', ''),
            'created_before': self.request.GET.get('created_before', ''),
            'rating': self.request.GET.get('rating', ''),
            'name_starts_with': self.request.GET.get('name_starts_with', ''),
            'popular_durations': self.request.GET.getlist('popular_durations', []),
            'hide_expensive': self.request.GET.get('hide_expensive', ''),
            'hide_without_reviews': self.request.GET.get('hide_without_reviews', ''),
            'hide_new': self.request.GET.get('hide_new', ''),
            'highly_rated': self.request.GET.get('highly_rated', ''),
            'exclude_duration': self.request.GET.get('exclude_duration', ''),
            'exclude_location': self.request.GET.get('exclude_location', ''),
            'has_guide': self.request.GET.get('has_guide', ''),
        }
        
        # Добавляем выборки для селектов
        context['duration_choices'] = Tour.DURATION_CHOICES
        
        return context

class TourCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Tour
    form_class = TourForm
    template_name = 'main/tour_form.html'
    success_url = reverse_lazy('tour_list')

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        if form.is_valid():
            tour = form.save(commit=False)
            image = request.FILES.get('image')
            if image:
                tour.image = image
            tour.save()
            messages.success(request, 'Тур успешно создан!')
            return redirect(self.success_url)
        return self.form_invalid(form)

class TourUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Tour
    form_class = TourForm
    template_name = 'main/tour_form.html'
    success_url = reverse_lazy('tour_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and self.request.user.role == 'Менеджер':
            if 'slot_form' not in context:
                context['slot_form'] = SlotForm()
            context['guides'] = self.object.guides.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        slot_form = SlotForm(request.POST) if 'add_slot' in request.POST else SlotForm()
        # Массовое создание слотов на 7 дней вперёд
        if 'add_week_slots' in request.POST and (request.user.is_superuser or request.user.role == 'Менеджер'):
            guide_id = request.POST.get('week_guide')
            time_str = request.POST.get('week_time')
            if guide_id and time_str:
                guide = Guide.objects.get(id=guide_id)
                hour, minute = map(int, time_str.split(':'))
                today = timezone.now().date()
                created = 0
                for i in range(7):
                    dt = timezone.make_aware(datetime.datetime.combine(today + timedelta(days=i), datetime.time(hour, minute)))
                    if not Slot.objects.filter(tour=self.object, guide=guide, datetime=dt).exists():
                        Slot.objects.create(tour=self.object, guide=guide, datetime=dt)
                        created += 1
                messages.success(request, f'Создано {created} слотов на 7 дней вперёд!')
            else:
                messages.error(request, 'Выберите гида и время!')
            return redirect('tour_edit', pk=self.object.pk)
        if 'add_slot' in request.POST and (request.user.is_superuser or request.user.role == 'Менеджер'):
            if slot_form.is_valid():
                slot = slot_form.save(commit=False)
                slot.tour = self.object
                slot.save()
                messages.success(request, 'Слот успешно добавлен!')
                return redirect('tour_edit', pk=self.object.pk)
            else:
                context = self.get_context_data(form=form, slot_form=slot_form)
                return self.render_to_response(context)
        if form.is_valid():
            tour = form.save(commit=False)
            image = request.FILES.get('image')
            if image:
                tour.image = image
            tour.save()
            messages.success(request, 'Тур успешно обновлен!')
            return redirect(self.success_url)
        return self.form_invalid(form)

class TourDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Tour
    template_name = 'main/tour_confirm_delete.html'
    success_url = reverse_lazy('tour_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Тур успешно удален!')
        return super().delete(request, *args, **kwargs)

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
    non_moscow_tours =Tour.objects.exclude(location__icontains='Москва')[:3]
    
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
    tour = get_object_or_404(Tour, id=tour_id)
    next_tours = tour.get_next_tours(3)
    prev_tours = tour.get_prev_tours(3)
    reviews = tour.reviews.select_related('user').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    similar_tours = Tour.objects.filter(
        Q(duration=tour.duration) | Q(location__icontains=tour.location)
    ).exclude(id=tour.id)[:4]
    price_range_min = float(tour.price) * 0.8
    price_range_max = float(tour.price) * 1.2
    price_similar_tours = Tour.objects.filter(
        price__range=(price_range_min, price_range_max)
    ).exclude(duration=tour.duration).distinct()[:3]
    
    booking_form = None
    booking_success = False
    booking_error = None
    if request.user.is_authenticated and request.user.role == 'Пользователь':
        if request.method == 'POST' and 'book_tour' in request.POST:
            booking_form = BookingForm(request.POST, tour=tour)
            if booking_form.is_valid():
                slot = booking_form.cleaned_data['slot']
                # Проверка: слот не занят
                if slot.is_booked:
                    booking_error = 'Этот слот уже занят. Пожалуйста, выберите другой.'
                else:
                    Booking.objects.create(user=request.user, tour=tour, date=slot.datetime, total_price=float(tour.price))
                    # Создаём Rental для пользователя по бронированию тура
                    Rental.objects.create(
                        user=request.user,
                        bike=slot.bike if hasattr(slot, 'bike') else None,
                        start_time=slot.datetime,
                        end_time=slot.datetime + timedelta(hours=tour.duration),
                        total_price=float(tour.price)
                    )
                    slot.is_booked = True
                    slot.save()
                    booking_success = True
                    booking_form = BookingForm(tour=tour)  # сброс формы
            else:
                booking_error = 'Проверьте правильность заполнения формы.'
        else:
            booking_form = BookingForm(tour=tour)

    return render(request, 'main/tour_detail.html', {
        'tour': tour,
        'next_tours': next_tours,
        'prev_tours': prev_tours,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'similar_tours': similar_tours,
        'price_similar_tours': price_similar_tours,
        'is_highly_rated': tour.is_highly_rated(),
        'booking_form': booking_form,
        'booking_success': booking_success,
        'booking_error': booking_error,
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

def permission_denied(request, exception):
    """Обработчик ошибки 403 (Доступ запрещен)"""
    return render(request, 'main/403.html', {'exception': str(exception)}, status=403)

# Пагинация
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# Валидация бизнес-логики: нельзя арендовать недоступный велосипед
class RentalViewSet(viewsets.ModelViewSet):
    queryset = Rental.objects.select_related('user', 'bike').all()
    serializer_class = RentalSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'bike', 'start_time', 'end_time', 'total_price']
    search_fields = ['user__username', 'bike__type']
    ordering_fields = ['start_time', 'end_time', 'total_price']

    def create(self, request, *args, **kwargs):
        bike_id = request.data.get('bike')
        if bike_id:
            bike = Bike.objects.filter(id=bike_id).first()
            if bike and bike.status.status_name != 'Доступен':
                return Response({'error': 'Велосипед недоступен для аренды.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    @action(methods=['GET'], detail=False)
    def my_rentals(self, request):
        user = request.user
        rentals = self.get_queryset().filter(user=user)
        serializer = self.get_serializer(rentals, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def expensive_or_long(self, request):
        # Аренды, где (цена > 1000 и пользователь не admin) или велосипед НЕ стандартный
        queryset = self.get_queryset().filter(
            (Q(total_price__gt=1000) & ~Q(user__username__icontains='admin')) |
            ~Q(bike__type='standard')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def active_not_electric(self, request):
        # Аренды, где (ещё не завершены и велосипед НЕ электрический) или пользователь НЕ manager
        queryset = self.get_queryset().filter(
            (Q(end_time__gte=timezone.now()) & ~Q(bike__type='electric')) |
            ~Q(user__role='manager')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class BikeViewSet(viewsets.ModelViewSet):
    queryset = Bike.objects.select_related('status', 'location').all()
    serializer_class = BikeSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status', 'location']
    search_fields = ['type', 'location__name']
    ordering_fields = ['rental_price_hour', 'rental_price_day']

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'gender']
    search_fields = ['username', 'email']
    ordering_fields = ['username', 'email'] 

@login_required
def slot_create(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    if request.user.role != 'Менеджер':
        return HttpResponseForbidden('Доступ разрешён только менеджерам')
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.tour = tour
            slot.save()
            messages.success(request, 'Слот успешно добавлен!')
            return redirect('tour_edit', pk=tour.id)
    else:
        form = SlotForm()
    return render(request, 'main/slot_form.html', {'form': form, 'tour': tour})

@login_required
def slot_update(request, slot_id):
    slot = get_object_or_404(Slot, id=slot_id)
    if request.user.role != 'Менеджер':
        return HttpResponseForbidden('Доступ разрешён только менеджерам')
    if request.method == 'POST':
        form = SlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Слот успешно обновлён!')
            return redirect('tour_edit', pk=slot.tour.id)
    else:
        form = SlotForm(instance=slot)
    return render(request, 'main/slot_form.html', {'form': form, 'tour': slot.tour})

@login_required
def slot_delete(request, slot_id):
    slot = get_object_or_404(Slot, id=slot_id)
    if request.user.role != 'Менеджер':
        return HttpResponseForbidden('Доступ разрешён только менеджерам')
    tour_id = slot.tour.id
    if request.method == 'POST':
        slot.delete()
        messages.success(request, 'Слот успешно удалён!')
        return redirect('tour_edit', pk=tour_id)
    return render(request, 'main/slot_confirm_delete.html', {'slot': slot})

class RentalCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Rental
    form_class = RentalForm
    template_name = 'main/rental_form.html'
    success_url = reverse_lazy('rental_list')

    def form_valid(self, form):
        rental = form.save(commit=False)
        rental.user = self.request.user
        rental.total_price = form.cleaned_data['total_price']
        rental.save()
        messages.success(self.request, 'Аренда успешно создана!')
        return redirect(self.success_url)

class RentalDeleteView(LoginRequiredMixin, DeleteView):
    model = Rental
    template_name = 'main/rental_confirm_delete.html'
    success_url = reverse_lazy('rental_list')

    def dispatch(self, request, *args, **kwargs):
        rental = self.get_object()
        user = request.user
        # Разрешено, если пользователь — владелец аренды, менеджер или суперпользователь
        if user == rental.user or user.is_superuser or user.role == 'Менеджер':
            return super().dispatch(request, *args, **kwargs)
        return HttpResponseForbidden('Доступ запрещён: можно удалять только свои аренды или если вы менеджер/админ.')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Аренда успешно удалена!')
        return super().delete(request, *args, **kwargs)

class RentalUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Rental
    form_class = RentalForm
    template_name = 'main/rental_form.html'
    success_url = reverse_lazy('rental_list')

    def form_valid(self, form):
        rental = form.save(commit=False)
        rental.user = self.request.user
        rental.total_price = form.cleaned_data.get('total_price', rental.total_price)
        rental.save()
        messages.success(self.request, 'Аренда успешно обновлена!')
        return redirect(self.success_url) 