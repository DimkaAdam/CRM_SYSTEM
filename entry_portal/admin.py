from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from .models import PortalCompany

class PortalCompanyAdminForm(forms.ModelForm):
    # Поле для ввода "сырого" пароля в админке (не сохраняется напрямую)
    raw_password = forms.CharField(
        label="Пароль компании (сырой)",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Оставь пустым, если не меняешь пароль. При сохранении будет захэширован."
    )

    class Meta:
        model = PortalCompany
        fields = ["name", "slug", "logo", "redirect_url", "is_active", "order", "raw_password"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        raw = self.cleaned_data.get("raw_password")
        if raw:  # если ввели новый сырой пароль — перехэшируем
            obj.shared_password = make_password(raw)
        if commit:
            obj.save()
        return obj

@admin.register(PortalCompany)
class PortalCompanyAdmin(admin.ModelAdmin):
    form = PortalCompanyAdminForm
    list_display = ("name", "slug", "redirect_url", "is_active", "order", "updated_at")
    list_editable = ("redirect_url", "is_active", "order")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    ordering = ("order", "name")
