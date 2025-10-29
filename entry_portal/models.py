from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password


class PortalCompany(models.Model):
    """
    Компания на стартовом экране entry_portal.
    У каждой компании теперь два общих пароля:
      - staff_password   → рабочие
      - manager_password → руководство
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    logo = models.ImageField(upload_to="entry_portal_logos/", blank=True, null=True)
    redirect_url = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    # 🔐 Отдельные хэши паролей
    staff_password = models.CharField(max_length=255, blank=True)
    manager_password = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # Установка/проверка паролей
    def set_staff_password(self, raw_password: str):
        self.staff_password = make_password(raw_password)
        self.save(update_fields=["staff_password", "updated_at"])

    def set_manager_password(self, raw_password: str):
        self.manager_password = make_password(raw_password)
        self.save(update_fields=["manager_password", "updated_at"])

    def check_staff_password(self, raw_password: str) -> bool:
        return bool(self.staff_password and check_password(raw_password, self.staff_password))

    def check_manager_password(self, raw_password: str) -> bool:
        return bool(self.manager_password and check_password(raw_password, self.manager_password))

