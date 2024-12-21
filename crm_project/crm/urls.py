from django.urls import path, include
from . import views
from .views import ClientCreateAPIView, DealCreateAPIView
from .views import ClientViewSet, DealViewSet
from rest_framework.routers import DefaultRouter

# Создаем один роутер для обоих ViewSet
router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'deals', DealViewSet, basename='deal')

urlpatterns = [
    path('', views.index, name='index'),
    path('clients/', views.client_list, name='client_list'),
    path('deals/', views.deal_list, name='deal_list'),
    path('tasks/', views.task_list, name='task_list'),
    path('pipelines/', views.pipeline_list, name='pipeline_list'),
    path('api/clients/', ClientCreateAPIView.as_view(), name='api_add_client'),  # Создание клиента через API
    path('api/deals/create/', DealCreateAPIView.as_view(), name='deal-create'),  # Создание сделки через API
    path('api/', include(router.urls)),  # Подключаем маршруты для ViewSets (клиенты и сделки)
    path('deals/export/', views.export_deals_to_excel, name='export_deals_to_excel'), # Exel
    path('sales_analytics/', views.sales_analytics, name='sales_analytics'),
]
