from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from .views import slot_create, slot_update, slot_delete, RentalCreateView

urlpatterns = [
    path('', views.index, name='index'),
    path('tours/', views.TourListView.as_view(), name='tour_list'),
    path('tours/create/', views.TourCreateView.as_view(), name='tour_create'),
    path('tours/<int:pk>/edit/', views.TourUpdateView.as_view(), name='tour_edit'),
    path('tours/<int:pk>/delete/', views.TourDeleteView.as_view(), name='tour_delete'),
    path('tours/<int:tour_id>/', views.tour_detail, name='tour_detail'),
    path('tours/<int:tour_id>/review/', views.create_review, name='create_review'),
    path('tours/bulk-actions/', views.bulk_tour_actions, name='bulk_tour_actions'),
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/create/', RentalCreateView.as_view(), name='rental_create'),
    path('rentals/<int:pk>/delete/', views.RentalDeleteView.as_view(), name='rental_delete'),
    path('tour-guides/', views.tour_guides_list, name='tour_guides_list'),
    path('exclude-examples/', views.exclude_examples, name='exclude_examples'),
    path('count-exists-examples/', views.count_exists_example, name='count_exists_examples'),
    
    # Аутентификация и профиль
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('tours/<int:tour_id>/slot/add/', slot_create, name='slot_create'),
    path('slot/<int:slot_id>/edit/', slot_update, name='slot_update'),
    path('slot/<int:slot_id>/delete/', slot_delete, name='slot_delete'),
]

router = DefaultRouter()
router.register(r'api/bikes', views.BikeViewSet)
router.register(r'api/rentals', views.RentalViewSet)
router.register(r'api/users', views.UserViewSet)

urlpatterns += router.urls

handler403 = 'main.views.permission_denied' 