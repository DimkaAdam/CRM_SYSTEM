from django.core.serializers import serialize
from django.shortcuts import render, redirect
from .models import Client, Deals, Task, PipeLine,CompanyPallets
from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import ClientSerializer
from .serializers import DealSerializer

import openpyxl
from django.http import HttpResponse

from django.db.models import Sum


def index(request):
    return render(request, 'crm/index.html')

def client_list(request):
    clients = Client.objects.all()

    supplier = clients.filter(client_type='suppliers')
    buyer = clients.filter(client_type = 'buyers')

    return render(request, 'crm/client_list.html', {
        'clients': clients,
        'suppliers': supplier,
        'buyers': buyer,
    })

def deal_list(request):
    deals = Deals.objects.all()
    return render(request, 'crm/deal_list.html', {'deals': deals})

def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'crm/task_list.html', {'tasks': tasks})

def pipeline_list(request):
    pipelines = PipeLine.objects.all()
    return render(request, 'crm/pipeline_list.html', {'pipelines': pipelines})

class ClientCreateAPIView(APIView):
    def post(self, request):
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

class DealCreateAPIView(APIView):
    def post(self, request):
        serializer = DealSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DealViewSet(viewsets.ModelViewSet):
    queryset = Deals.objects.all()
    serializer_class = DealSerializer

def export_deals_to_excel(request):
    # Создаем новый Excel-файл
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Deals'

    # Заголовки столбцов
    columns = [
        'Date', 'Supplier', 'Buyer', 'Grade', 'Shipped Quantity', 'Shipped Pallets',
        'Received Quantity', 'Received Pallets', 'Supplier Price', 'Supplier Total','Buyer Price',
        'Transport Cost', 'Transport Company','Total Amount', 'Total Income/Loss'
    ]
    for col_num, column_title in enumerate(columns, 1):
        worksheet.cell(row=1, column=col_num, value=column_title)

    # Получаем все сделки из базы данных
    deals = Deals.objects.all()

    # Добавляем строки с данными сделок
    for row_num, deal in enumerate(deals, 2):
        worksheet.cell(row=row_num, column=1, value=deal.date.strftime("%Y-%m-%d"))
        worksheet.cell(row=row_num, column=2, value=deal.supplier)
        worksheet.cell(row=row_num, column=3, value=deal.buyer)
        worksheet.cell(row=row_num, column=4, value=deal.grade)
        worksheet.cell(row=row_num, column=5, value=deal.shipped_quantity)
        worksheet.cell(row=row_num, column=6, value=deal.shipped_pallets)
        worksheet.cell(row=row_num, column=7, value=deal.received_quantity)
        worksheet.cell(row=row_num, column=8, value=deal.received_pallets)
        worksheet.cell(row=row_num, column=9, value=deal.supplier_price)
        worksheet.cell(row=row_num, column=10, value=deal.supplier_total)
        worksheet.cell(row=row_num, column=11, value=deal.buyer_price)
        worksheet.cell(row=row_num, column=12, value=deal.transport_cost)
        worksheet.cell(row=row_num, column=12, value=deal.transport_company)
        worksheet.cell(row=row_num, column=13, value=deal.total_amount)
        worksheet.cell(row=row_num, column=14, value=deal.total_income_loss)

    # Настраиваем ответ для скачивания файла
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="deals.xlsx"'

    workbook.save(response)
    return response



def sales_analytics(request):
    # Данные о сделках
    suppliers_income = Deals.objects.values('supplier').annotate(total_income_loss=Sum('total_income_loss'))
    suppliers_income_dict = {entry['supplier']: float(entry['total_income_loss'] or 0) for entry in suppliers_income}

    total_deals = Deals.objects.count()
    total_income = Deals.objects.filter(total_income_loss__gt=0).aggregate(Sum('total_income_loss'))['total_income_loss__sum'] or 0
    total_loss = Deals.objects.filter(total_income_loss__lt=0).aggregate(Sum('total_income_loss'))['total_income_loss__sum'] or 0

    # Данные о палетах
    company_pallets = CompanyPallets.objects.select_related('company_name')

    # Сброс палет (если пользователь отправил форму)
    if request.method == 'POST' and 'reset_pallets' in request.POST:
        CompanyPallets.objects.update(pallets_count=0)

    context = {
        'suppliers_income': suppliers_income_dict,
        'total_deals': total_deals,
        'total_income': total_income,
        'total_loss': total_loss,
        'company_pallets': company_pallets,
    }
    return render(request, 'crm/sales_analytics.html', context)

