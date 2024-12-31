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
    path('deals/export/', views.export_deals_to_excel, name='export_deals_to_excel'),  # Exel
    path('sales_analytics/', views.sales_analytics, name='sales_analytics'),
    path('contacts/', views.contacts_view, name='contacts_list'),
    path('employees/<int:contact_id>/', views.manage_employees, name='manage_employees'),
    path('contacts/<int:contact_id>/employees/', views.load_employees, name='load_employees'),
    path('contacts/<int:contact_id>/add_employee/', views.add_employee, name='add_employee'),
    path('contacts/<int:employee_id>/delete_employee/', views.delete_employee, name='delete_employee'),
    path('contacts/add/', views.add_contact, name='add_contact'),

    # Маршруты для работы с компаниями
    path('companies/', views.company_list, name='company_list'),  # Список компаний
    path('companies/add/', views.add_company, name='add_company'),

    path('companies/<int:company_id>/', views.company_detail, name='company_detail'),
    path('company/<int:company_id>/edit/', views.edit_company, name='edit_company'),
    path('company/<int:company_id>/delete/', views.delete_company, name='delete_company'),
    path('companies/', views.company_list, name='company_main'),

    path('contacts/add/<int:company_id>/', views.add_contact, name='add_contact'),
    path('companies/<int:contact_id>/edit/', views.edit_contact, name='edit_contact'),
    path('companies/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
    path('contact/view/<int:id>/', views.view_contact, name='view_contact'),


    # Управление сотрудниками компании
    path('companies/<int:company_id>/employees/<int:employee_id>/delete/', views.delete_employee,
         name='delete_employee_from_company'),  # Удаление сотрудника из компании
]
