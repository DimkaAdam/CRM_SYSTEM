from django.contrib import admin
from .models import Client, Deals, Task, PipeLine

admin.site.register(Client)
admin.site.register(Deals)
admin.site.register(Task)

@admin.register(PipeLine)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_company_name', 'stage', 'created_at')

    def client_company_name(self, obj):
        return obj.client.company if obj.client else 'No company'

    client_company_name.admin_order_field = 'client__company'  # Сортировка по полю компании
    client_company_name.short_description = 'Company'  # Заголовок для колонки