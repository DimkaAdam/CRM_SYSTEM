from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    ClientCreateAPIView, DealCreateAPIView,
    ClientViewSet, DealViewSet, export_company_report_pdf,
    get_deal_by_ticket, export_scale_ticket_pdf,add_contact,task_list, get_events, add_event, delete_event,
    get_licence_plates,get_grades,get_scheduled_shipments,add_scheduled_shipment,delete_scheduled_shipment,generate_bol_pdf,update_stage,
    get_bol_counters, increment_bol_counters,get_clients_grouped, get_scale_ticket_counters,increment_scale_ticket_counters,mark_shipment_done,

)


# 📌 Роутер для API
router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'deals', DealViewSet, basename='deal')


# 📌 Основные маршруты
urlpatterns = [
    path("", views.index, name="index"),
    path("clients/", views.client_list, name="client_list"),
    path("deals/", views.deal_list, name="deal_list"),
    path("tasks/", views.task_list, name="task_list"),
    path('companies/', views.company_list, name='company_list'),
    path('companies/', views.company_list, name='company_main'),
    path('contact/<int:id>/view/', views.view_contact, name='view_contact'),


    # 📌 React Kanban-доска
    path("api/update_stage/", views.update_stage, name="update_stage"),
    path("kanban/", views.kanban_board, name="kanban_board"),
    path("api/update_stage/", update_stage, name="update_stage"),




    # 📌 API для работы с клиентами и сделками
    path("api/clients/", ClientCreateAPIView.as_view(), name="api_add_client"),
    path("api/deals/create/", DealCreateAPIView.as_view(), name="deal-create"),
    path("api/", include(router.urls)),

    # 📌 Экспорт данных
    path("deals/export/", views.export_deals_to_excel, name="export_deals_to_excel"),
    path("sales_analytics/", views.sales_analytics, name="sales_analytics"),
    path("contacts/", views.contacts_view, name="contacts_list"),

    # 📌 Работа с компаниями
    path("companies/", views.company_list, name="company_list"),
    path("companies/add/", views.add_company, name="add_company"),
    path("companies/<int:company_id>/", views.company_detail, name="company_detail"),
    path("company/<int:company_id>/edit/", views.edit_company, name="edit_company"),
    path("company/<int:company_id>/delete/", views.delete_company, name="delete_company"),
    path("companies/<int:company_id>/employees/<int:employee_id>/delete/", views.delete_employee, name="delete_employee_from_company"),
    path("contacts/<int:contact_id>/add-material/", views.add_contact_material, name="add_contact_material"),
    path("contact-material/<int:pk>/edit/", views.edit_contact_material, name="edit_contact_material"),
    path('companies/<int:contact_id>/edit/', views.edit_contact, name='edit_contact'),
    path('contacts/add/<int:company_id>/', add_contact, name='add_contact'),
    path('api/licence-plates/', get_licence_plates, name='get_licence_plates'),
    path('api/get_price/', views.get_price_by_supplier_and_grade, name='get_price_by_supplier_and_grade'),
    path('api/get_buyer_price/', views.get_price_by_buyer_and_grade, name='get_price_by_buyer_and_grade'),





    # 📌 Управление сотрудниками
    path("contacts/<int:contact_id>/add-material/", views.add_contact_material, name="add_contact_material"),
    path("contact-material/<int:pk>/edit/", views.edit_contact_material, name="edit_contact_material"),
    path("companies/<int:company_id>/employees/<int:employee_id>/delete/", views.delete_employee, name="delete_employee_from_company"),
    path("employees/<int:contact_id>/", views.manage_employees, name="manage_employees"),
    path("contacts/<int:contact_id>/employees/", views.load_employees, name="load_employees"),
    path("contacts/<int:contact_id>/add_employee/", views.add_employee, name="add_employee"),
    path("contacts/<int:employee_id>/delete_employee/", views.delete_employee, name="delete_employee"),
    path("contacts/<int:employee_id>/edit_employee/", views.edit_employee, name="edit_employee"),



    # 📌 Работа с сделками
    path("deals/", views.deal_list, name="deal_list"),
    path("deals/<int:deal_id>/", views.get_deal_details, name="get_deal_details"),
    path("deals/<int:deal_id>/edit/", views.edit_deal, name="edit_deal"),
    path("deals/<int:deal_id>/delete/", views.delete_deal, name="delete_deal"),

    # 📌 Отчёты
    path("reports/", views.report_list, name="report_list"),




    path("reports/company/", views.company_report, name="company_report"),

    # HTML отчёт по поставщикам
    path("reports/supply/", views.supply_list, name="supply_list"),

    # PDF экспорт по поставщикам
    path("reports/company/pdf/", views.export_supply_list_pdf, name="export_supply_list_pdf"),
    path("reports/company/pdf/", export_company_report_pdf, name="export_company_report_pdf"),
    path("get-deal-by-ticket/", get_deal_by_ticket, name="get_deal_by_ticket"),
    path("export-scale-ticket/", export_scale_ticket_pdf, name="export_scale_ticket"),

     #Tasks
    path("tasks/", task_list, name="task_list"),
    path("api/events/", get_events, name="get_events"),
    path("api/events/add/", add_event, name="add_event"),
    path("api/events/delete/<int:event_id>/", delete_event, name="delete_event"),
    path("api/grades/", get_grades, name="get_grades"),  # ✅ Новый API
    path("api/scheduled-shipments/", get_scheduled_shipments, name="get_scheduled_shipments"),
    path("api/scheduled-shipments/add/", add_scheduled_shipment, name="add_scheduled_shipment"),
    path("api/scheduled-shipments/delete/<int:shipment_id>/", delete_scheduled_shipment,
       name="delete_scheduled_shipment"),
    path('generate-bol-pdf/', generate_bol_pdf, name='generate_bol_pdf'),
    path("company/<int:id>/toggle-pickup/", views.toggle_pickup, name="toggle_pickup"),

    path('api/bol-counters/', get_bol_counters, name='get_bol_counters'),
    path('api/bol-counters/increment/', increment_bol_counters, name='increment_bol_counters'),
    path("api/clients/", get_clients_grouped, name="get_clients_grouped"),
    path("api/companies-by-type/", views.get_companies_by_type),
    path('api/scale-ticket-counters/', get_scale_ticket_counters, name='get_scale_ticket_counters'),
    path('api/scale-ticket-counters/increment/', views.increment_scale_ticket_counters, name='increment_scale_ticket_counters'),
    path('api/scheduled-shipments/done/<int:shipment_id>/', mark_shipment_done, name='mark_shipment_done'),

    path('contacts/<int:contact_id>/tasks/', views.contact_tasks, name='contact_tasks'),

    path('contacts/<int:contact_id>/tasks/add/', views.add_task, name='add_task'),









] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
