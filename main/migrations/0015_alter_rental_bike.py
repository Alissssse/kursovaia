# Generated by Django 4.2 on 2025-06-24 17:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_slot_bike'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rental',
            name='bike',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rentals', to='main.bike', verbose_name='Велосипед'),
        ),
    ]
