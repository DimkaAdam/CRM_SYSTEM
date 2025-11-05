from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = "scales"

# ==== API ====
api_received_patterns = [
    path("", views.api_list_received, name="api_received_list"),
    path("create/", views.api_create_received, name="api_received_create"),
    path("<int:pk>/update/", views.api_update_received, name="api_received_update"),
    path("<int:pk>/delete/", views.api_delete_received, name="api_received_delete"),
]

# ==== Основные страницы ====
urlpatterns = [
    # Главная страница весов (с интерфейсом)
    path("", views.home, name="home"),
    path("home/", views.home, name="home_alias"),  # алиас для совместимости старых ссылок

    # Группа API
    path("api/received/", include(api_received_patterns)),

    # Экспорт и выход
    path("export/daily/", views.export_daily_pdf, name="export_daily_pdf"),
    path("export/monthly/", views.export_monthly_excel, name="export_monthly_excel"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
]
