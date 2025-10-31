from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'scales'

urlpatterns = [
    path('home/', views.home, name='home'),
    path("api/received/", views.api_list_received, name="api_received_list"),
    path("api/received/create/", views.api_create_received, name="api_received_create"),
    path("api/received/<int:pk>/update/", views.api_update_received, name="api_received_update"),
    path("api/received/<int:pk>/delete/", views.api_delete_received, name="api_received_delete"),

    path("export/daily/", views.export_daily_pdf, name="export_daily_pdf"),
    path("export/monthly/", views.export_monthly_excel, name="export_monthly_excel"),
    path("logout/", auth_views.LogoutView.as_view(next_page='/'), name="logout"),

]

