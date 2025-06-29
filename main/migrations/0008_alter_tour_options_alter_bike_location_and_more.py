# Generated by Django 5.1.2 on 2025-05-09 19:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Миграция для изменения опций тура и локации велосипеда."""

    dependencies = [
        ('main', '0007_tour_created_at_tour_updated_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tour',
            options={'ordering': ['-created_at'], 'verbose_name': 'Маршрут', 'verbose_name_plural': 'Маршруты'},
        ),
        migrations.AlterField(
            model_name='bike',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bikes', to='main.location', verbose_name='Локация'),
        ),
        migrations.AlterField(
            model_name='bike',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bikes', to='main.bikestatus', verbose_name='Статус'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='tour',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='main.tour', verbose_name='Тур'),
        ),
        migrations.AlterField(
            model_name='booking',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='guide',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='guide_profile', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='guidetour',
            name='guide',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guide_tours', to='main.guide', verbose_name='Гид'),
        ),
        migrations.AlterField(
            model_name='guidetour',
            name='tour',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guide_tours', to='main.tour', verbose_name='Тур'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='rental',
            name='bike',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rentals', to='main.bike', verbose_name='Велосипед'),
        ),
        migrations.AlterField(
            model_name='rental',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rentals', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='review',
            name='tour',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='main.tour', verbose_name='Тур'),
        ),
        migrations.AlterField(
            model_name='review',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь'),
        ),
        migrations.AlterField(
            model_name='tour',
            name='duration',
            field=models.IntegerField(
                choices=[
                    (1, '1 час'),
                    (2, '2 часа'),
                    (3, '3 часа'),
                    (4, '4 часа'),
                    (6, '6 часов'),
                    (8, '8 часов (целый день)'),
                    (12, '12 часов'),
                    (24, '24 часа (сутки)')
                ],
                verbose_name='Длительность (часы)'
            ),
        ),
    ]
