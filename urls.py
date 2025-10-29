from django.contrib import admin
from django.urls import path, include
from entry_portal import views as portal_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('crm.urls')),  # Подключаем маршруты из crm

]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("entry_portal.urls")),  # 👈 добавляем сюда наш портал
    path("crm/", include("crm.urls")),       # твоя CRM
    path("scales/", include("scales.urls")), # (если будет модуль весов)

    # 👇 Один общий логин по паролю компании (без логина)
    path("login", portal_views.company_login, name="company_login_alias"),
]
