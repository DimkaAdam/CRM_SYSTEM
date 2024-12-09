from django.contrib import admin
from .models import Client, Deals, Task, PipeLine

admin.site.register(Client)
admin.site.register(Deals)
admin.site.register(Task)

@admin.register(PipeLine)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ('name', 'stage', 'created_at', 'updated_at')
    search_fields = ('name','stage')
