from django.contrib import admin
from .models import ReceivedMaterial

@admin.register(ReceivedMaterial)
class ReceivedMaterialAdmin(admin.ModelAdmin):
    list_display = ("date","material","gross_kg","net_kg","supplier","tag","company_slug","created_by","created_at")
    list_filter  = ("date","material","supplier","company_slug")
    search_fields = ("supplier","tag")