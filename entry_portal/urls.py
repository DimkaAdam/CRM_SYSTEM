from django.urls import path               # стандартный импорт для маршрутов
from . import views                        # импортируем функции из views.py

app_name = "entry_portal"                  # пространство имён для URL-ов (удобно в шаблонах)

urlpatterns = [
    path("", views.choose_company, name="choose_company"),       # экран выбора компании
    path("set/<slug:slug>/", views.set_company, name="set_company"),  # установка сессии и редирект
    path("login/", views.company_login, name="company_login"),   # ← новый
]

