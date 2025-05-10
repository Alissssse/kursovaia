from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

# лаба 1: Демонстрация использования сеансов Django
urlpatterns = [
    path('admin/', admin.site.urls),
    # Включаем URLs приложения main с демонстрацией сеансов
    path('', include('main.urls')),
    # лаба 1: Добавляем URL-маршруты для аутентификации
    path('accounts/', include('django.contrib.auth.urls')),
    # лаба 1: Добавляем URL-маршрут для выхода
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # лаба 1: Настройка раздачи медиафайлов 

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns 
