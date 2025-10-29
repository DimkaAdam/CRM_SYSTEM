from django.utils import timezone
from datetime import timedelta

CUTOFF_HOUR = 19  # 19:00 по Ванкуверу

def business_day(dt=None):
    """Возвращает дату делового дня (меняется в 19:00)."""
    tz = timezone.get_current_timezone()
    now_local = (dt or timezone.now()).astimezone(tz)
    base_date = now_local.date()
    # если время >= 19:00, считаем что день уже следующий
    return base_date if now_local.hour < CUTOFF_HOUR else (base_date + timedelta(days=1))
