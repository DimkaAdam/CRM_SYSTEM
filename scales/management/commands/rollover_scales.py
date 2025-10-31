from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from scales.models import ReceivedMaterial
from scales.utils import business_day

class Command(BaseCommand):
    help = "Закрывает текущий отчётный день и открывает новый (срез в 19:00 по Ванкуверу)."

    def handle(self, *args, **options):
        tz = timezone.get_current_timezone()
        now_local = timezone.now().astimezone(tz)

        # Текущий и предыдущий бизнес-дни
        today_bd = business_day(now_local)
        prev_bd = today_bd - timedelta(days=1)

        # Отладочная информация в лог
        self.stdout.write(f"🕖 Запуск rollover: {now_local}")
        self.stdout.write(f"📅 Текущий бизнес-день: {today_bd}, предыдущий: {prev_bd}")

        # Здесь можно добавить код, если нужно что-то переносить, архивировать и т.п.
        # В нашем случае ничего не переносим — просто фиксируем лог.
        count_today = ReceivedMaterial.objects.filter(report_day=today_bd).count()
        count_prev = ReceivedMaterial.objects.filter(report_day=prev_bd).count()

        self.stdout.write(f"📦 Записей сегодня: {count_today}, вчера: {count_prev}")
        self.stdout.write(self.style.SUCCESS("✅ Смена закрыта успешно (логическая отсечка 19:00)"))
