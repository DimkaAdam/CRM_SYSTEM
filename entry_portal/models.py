# Импорт базовых инструментов
from django.db import models                     # поля и базовый класс модели
from django.utils.text import slugify            # автогенерация slug из name
from django.urls import reverse                  # если понадобится get_absolute_url
from django.contrib.auth.hashers import (        # для хранения/проверки хэша пароля
    make_password, check_password
)

class PortalCompany(models.Model):
    """
    Компания, отображаемая на стартовом экране entry_portal.
    Для каждой компании можно задать общий пароль (shared_password), по которому
    пользователи будут входить без индивидуальных аккаунтов.
    """

    # Отображаемое имя компании
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Отображаемое имя компании на стартовой странице."
    )

    # Короткий ключ (для URL/сессии), например: local-to-global, pmb-depot
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Ключ компании для маршрутизации (пример: local-to-global)."
    )

    # Логотип (необязателен)
    logo = models.ImageField(
        upload_to="entry_portal_logos/",
        blank=True,
        null=True,
        help_text="Логотип компании."
    )

    # Куда перенаправлять после выбора (можно относительный путь ИЛИ абсолютный URL)
    # Примеры: "/crm/dashboard", "/scales/home", "https://example.com/app"
    redirect_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Куда перенаправлять после выбора (пример: /crm/dashboard или /scales/home)."
        # Важно: НЕ ставим URLValidator, чтобы разрешить относительные пути!
    )

    # Активность (чтобы можно было временно скрывать)
    is_active = models.BooleanField(
        default=True,
        help_text="Если выключено — компания не показывается на экране выбора."
    )

    # Порядок сортировки (меньше — выше)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Порядок отображения на экране выбора (меньше число — выше)."
    )

    # 🔐 Хэш общего пароля для входа в эту компанию (без логина)
    # Храним ТОЛЬКО хэш! Сырой пароль никуда не пишем.
    shared_password = models.CharField(
        max_length=255,
        blank=True,
        help_text="Хэш общего пароля компании (задаётся через админку/скрипт)."
    )

    # Тех. поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Компания портала"
        verbose_name_plural = "Компании портала"
        ordering = ["order", "name"]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(slug=""),
                name="entryportal_slug_not_empty"
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
        # Автогенерация slug из name при необходимости
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("entry_portal:company_detail", kwargs={"slug": self.slug})

    # Удобные хелперы, если захочешь ставить/проверять пароль из кода (не обязательно)
    def set_shared_password(self, raw_password: str):
        """Захэшировать и сохранить общий пароль компании."""
        self.shared_password = make_password(raw_password)
        self.save(update_fields=["shared_password", "updated_at"])

    def check_shared_password(self, raw_password: str) -> bool:
        """Проверить сырой пароль против сохранённого хэша."""
        if not self.shared_password:
            return False
        return check_password(raw_password, self.shared_password)
