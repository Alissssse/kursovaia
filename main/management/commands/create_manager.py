from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from main.models import User  # Используем нашу кастомную модель пользователя

class Command(BaseCommand):
    help = 'Создает пользователя-менеджера'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя')
        parser.add_argument('email', type=str, help='Email пользователя')
        parser.add_argument('password', type=str, help='Пароль пользователя')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        try:
            with transaction.atomic():
                # Создаем пользователя
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_staff=True  # Даем доступ к админке
                )

                # Получаем или создаем группу менеджеров
                manager_group, created = Group.objects.get_or_create(name='Managers')
                
                # Добавляем пользователя в группу
                user.groups.add(manager_group)

                self.stdout.write(
                    self.style.SUCCESS(f'Успешно создан менеджер: {username}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при создании менеджера: {str(e)}')
            ) 