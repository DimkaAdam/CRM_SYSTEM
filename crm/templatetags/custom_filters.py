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


@register.filter
def range_filter(start, end):
    try:
        start = int(start)
        end = int(end)
        return range(start, end)
    except (ValueError, TypeError):
        return []

