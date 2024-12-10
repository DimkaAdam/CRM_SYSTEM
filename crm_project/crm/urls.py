from django.urls import path
from .import views
from .views import ClientCreateAPIView

urlpatterns = [
    path('', views.index, name='index'),
    path('clients/', views.client_list, name='client_list'),
    path('deals/', views.deal_list, name='deal_list'),
    path('tasks/', views.task_list, name='task_list'),
    path('pipelines/', views.pipeline_list, name='pipeline_list'),
    path('api/clients', ClientCreateAPIView.as_view(), name = 'api_add_client'),


]