from django.db import models                     # базовые классы моделей
from django.contrib.auth import get_user_model   # ссылка на пользователя (кто ввёл)
from .utils import business_day
from django.utils import timezone

class ReceivedMaterial(models.Model):
    # Дата приёма (по умолчанию — сегодня)
    date = models.DateField(auto_now_add=True)   # можно потом сделать ввод вручную
    report_day = models.DateField(db_index=True, null=True, blank=True)

    # Краткое имя материала: CB / SOP / OCC
    material = models.CharField(max_length=32)   # хранит "CB" и т.п.

    # Вес брутто и нетто (кг)
    gross_kg = models.DecimalField(max_digits=8, decimal_places=1)  # например 12345.6
    net_kg   = models.DecimalField(max_digits=8, decimal_places=1)

    # Поставщик (строкой на первом этапе)
    supplier = models.CharField(max_length=64)

    # Бирка / Tag №
    tag = models.CharField(max_length=32)

    # Какую компанию выбрали на портале (чтобы данные были изолированы)
    company_slug = models.SlugField(max_length=100)  # берём из request.session["company_slug"]

    # Кто внёс запись (удобно для аудита)
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True
    )

    # Метки времени
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        from .utils import business_day
        if not self.report_day:
            self.report_day = business_day(self.created_at)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]  # новые выше

    def __str__(self):
        return f"{self.date} {self.material} {self.net_kg}kg [{self.supplier}]"

    class ReceivedMaterial(models.Model):
        ...

        def save(self, *args, **kwargs):
            if not self.report_day:
                # если объект уже создан, возьмём created_at; иначе — текущее время
                dt = getattr(self, "created_at", None) or timezone.now()
                self.report_day = business_day(dt)
            super().save(*args, **kwargs)
