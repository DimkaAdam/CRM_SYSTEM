from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import PortalCompany

class PortalCompanyAdminForm(forms.ModelForm):
    # “Сырые” поля для ввода (хэш в БД писать не показываем)
    staff_password_raw   = forms.CharField(label="Пароль для Staff",   widget=forms.PasswordInput, required=False)
    manager_password_raw = forms.CharField(label="Пароль для Managers",widget=forms.PasswordInput, required=False)

    class Meta:
        model  = PortalCompany
        fields = ["name","slug","logo","redirect_url","is_active","order"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        sp  = self.cleaned_data.get("staff_password_raw")
        mp  = self.cleaned_data.get("manager_password_raw")
        if sp:
            obj.staff_password = make_password(sp)
        if mp:
            obj.manager_password = make_password(mp)
        if commit:
            obj.save()
        return obj

@admin.register(PortalCompany)
class PortalCompanyAdmin(admin.ModelAdmin):
    form = PortalCompanyAdminForm
    list_display  = ("name","slug","is_active","order")
    list_editable = ("order",)
    search_fields = ("name","slug")
    fields = ("name","slug","logo","redirect_url","is_active","order",
              "staff_password_raw","manager_password_raw")