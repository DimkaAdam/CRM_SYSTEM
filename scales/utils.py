from datetime import datetime, timedelta
from django.utils import timezone

CUTOFF_HOUR = 19  # 19:00 по Ванкуверу

def business_day(dt=None):
    """Возвращает дату делового дня (меняется в 19:00)."""
    tz = timezone.get_current_timezone()
    now_local = (dt or timezone.now()).astimezone(tz)
    base_date = now_local.date()
    # если время >= 19:00, считаем что день уже следующий
    return base_date if now_local.hour < CUTOFF_HOUR else (base_date + timedelta(days=1))


CUTOFF_HOUR = 19  # 19:00 по Ванкуверу

def current_window(now=None):
    tz = timezone.get_current_timezone()
    now_local = (now or timezone.now()).astimezone(tz)
    d = now_local.date()
    cutoff = timezone.make_aware(datetime(d.year, d.month, d.day, CUTOFF_HOUR, 0, 0), tz)
    if now_local < cutoff:
        start = cutoff - timedelta(days=1)
        end   = cutoff
    else:
        start = cutoff
        end   = cutoff + timedelta(days=1)
    return start, end

def previous_window(now=None):
    start, end = current_window(now)
    return start - timedelta(days=1), start