from django.contrib import admin
from .models import Client, Deals, Task, PipeLine

# Регистрируем стандартные модели
admin.site.register(Client)
admin.site.register(Deals)
admin.site.register(Task)

@admin.register(PipeLine)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ('company_display', 'stage')  # Используем существующую функцию

    def company_display(self, obj):
        return obj.company.name if obj.company else 'No company'

    company_display.admin_order_field = 'company__name'  # Сортировка по названию компании
    company_display.short_description = 'Company'  # Название колонки в админке