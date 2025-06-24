"""
Пользовательские шаблонные теги для bike tours.
"""
from django import template
from main.models import Tour

register = template.Library()

@register.inclusion_tag('main/partials/user_greeting.html', takes_context=True)
def show_user_greeting(context):
    """
    Получаем объект user из текущего контекста
    Возвращаем словарь, который будет контекстом для шаблона user_greeting.html
    """
    # Получаем объект user из текущего контекста
    user = context.get('user')
    # Возвращаем словарь, который будет контекстом для шаблона user_greeting.html
    return {'current_user': user}

@register.simple_tag
def top_tours(count=3):
    """
    Возвращает список самых популярных туров
    Параметр count определяет количество возвращаемых туров
    """
    return Tour.objects.all().order_by('-price')[:count]

@register.filter
def get_range(value):
    """
    Фильтр для создания диапазона чисел.
    Используется для отображения звездочек рейтинга.
    """
    try:
        value = int(value)
        return range(value)
    except (ValueError, TypeError):
        return range(0) 