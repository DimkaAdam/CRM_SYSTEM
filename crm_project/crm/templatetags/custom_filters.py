from django import template
import calendar

register = template.Library()

@register.filter(name='get_month_name')
def get_month_name(value):
    try:
        # Преобразует номер месяца в его название
        return calendar.month_name[int(value)]
    except (ValueError, IndexError):
        return value