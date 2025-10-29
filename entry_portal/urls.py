from django.urls import path
from . import views

app_name = "entry_portal"

urlpatterns = [
    path("", views.choose_company, name="choose_company"),  # экран выбора компании
    path("login/<slug:slug>/", views.portal_login, name="portal_login"),  # логин с паролем staff/manager
]
