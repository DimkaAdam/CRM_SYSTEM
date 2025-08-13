from django.core.serializers import serialize
import os
from .models import Client, Deals, Task, PipeLine, CompanyPallets, Company, Contact, Employee, ContactMaterial,ScheduledShipment,SCaleTicketStatus,TruckProfile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from .forms import TaskForm
from .serializers import ClientSerializer,DealSerializer,PipeLineSerializer

from .forms import ContactForm, CompanyForm, ContactMaterialForm, DealForm
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models.functions import ExtractYear, ExtractMonth
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.db.models import Q
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from django.views.decorators.http import require_POST
import json
from decimal import Decimal


from datetime import datetime,timezone,timedelta
from django.utils import timezone as t
from io import BytesIO

from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from .google_calendar import get_calendar_events
import glob

from .models import Event

import re

def sanitize_filename(name):
    name = name.strip()
    name = name.replace(' ', '_')
    return re.sub(r'[<>:"/\\|?*]', '_', name)



from django.conf import settings
print("📦 Current database path:", settings.DATABASES['default']['NAME'])


def index(request):
    return render(request, 'crm/index.html')


def client_list(request):
    clients = Client.objects.all()

    supplier = clients.filter(client_type='suppliers')
    buyer = clients.filter(client_type='buyers')
    hauler = clients.filter(client_type='hauler')
    return render(request, 'crm/client_list.html', {
        'clients': clients,
        'suppliers': supplier,
        'buyers': buyer,
        'hauler': hauler,
    })


def company_list(request):
    companies = Company.objects.all()
    return render(request, 'crm/company_ main.html', {'companies': companies})


def add_company(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            company = Company.objects.create(name=name)
            # Перенаправляем пользователя на страницу добавления контакта для этой компании
            return redirect('add_contact', company_id=company.id)

    return render(request, 'crm/add_company.html')

# Редактирование компании

def company_detail(request, company_id):
    # Получаем объект компании по id
    company = get_object_or_404(Company, id=company_id)

    # Получаем все контакты этой компании
    contacts = company.contacts.all()

    return render(request, 'crm/company_detail.html', {
        'company': company,
        'contacts': contacts,
    })

def edit_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_detail', company_id=company.id)
    else:
        form = CompanyForm(instance=company)
    return render(request, 'crm/edit_company.html', {'form': form, 'company': company})

def delete_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        company.delete()
        return redirect('company_list')  # После удаления перенаправляем на список компаний
    return render(request, 'crm/delete_company.html', {'company': company})


# Редактирование контакта
def edit_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)

    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            return redirect('company_list')  # Перенаправить на список компаний
    else:
        form = ContactForm(instance=contact)

    return render(request, 'crm/edit_contact.html', {'form': form, 'contact': contact})


# Удаление контакта
def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)

    # Удаляем контакт
    contact.delete()

    # Перенаправляем обратно на список компаний
    return redirect('Contacts')  # Указываем имя маршрута для списка компаний

def view_contact(request, id):
    contact = get_object_or_404(Contact, id=id)
    pipeline, _ = PipeLine.objects.get_or_create(contact=contact)

    if request.method == "POST":
        # 🎯 Обработка смены стадии
        if "change_stage" in request.POST:
            stage = request.POST.get("stage")
            pipeline.stage = stage
            pipeline.save()

        # 🎯 Обработка формы редактирования контакта
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()

            # 🟡 Сохраняем чекбокс
            pickup_requested = request.POST.get("pickup_requested") == "on"
            contact.company.pickup_requested = pickup_requested
            contact.company.save()

        return redirect("view_contact", id=contact.id)

    else:
        form = ContactForm(instance=contact)

    employees = contact.employees.all()
    trucks = TruckProfile.objects.filter(company=contact.company)

    return render(request, 'crm/view_contact.html', {
        'contact': contact,
        'form': form,
        'employees': employees,
        'pipeline': pipeline,
        'company': contact.company,
        'trucks': trucks,
    })


@csrf_exempt
def toggle_pickup(request, id):
    if request.method == "POST":
        import json
        company = get_object_or_404(Company, id=id)
        data = json.loads(request.body)
        company.pickup_requested = data.get('pickup_requested', False)
        company.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)

def manage_employees(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    contacts = company.contacts.all()

    if request.method == 'POST':
        contact_id = request.POST.get('contact_id')
        contact = get_object_or_404(Contact, id=contact_id)

        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        position = request.POST.get('position')

        Employee.objects.create(
            contact=contact,
            name=name,
            email=email,
            phone=phone,
            position=position
        )

        return redirect('manage_employees', company_id=company.id)

    return render(request, 'crm/manage_employees.html', {'company': company, 'contacts': contacts})

def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        employee.name = request.POST.get('name')
        employee.email = request.POST.get('email')
        employee.phone = request.POST.get('phone')
        employee.position = request.POST.get('position')
        employee.save()
        return redirect('view_contact', id=employee.contact.id)

    return render(request, 'crm/edit_employee.html', {'employee': employee})


def get_employees(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    employees = Employee.objects.filter(contact__company=company)

    # Возвращаем данные сотрудников в формате JSON
    employees_data = [
        {
            'name': employee.name,
            'email': employee.email,
            'phone': employee.phone,
            'position': employee.position,
        }
        for employee in employees
    ]

    return JsonResponse({'employees': employees_data})


def contacts_view(request):
    companies = Company.objects.prefetch_related('contacts').all()
    return render(request, 'crm/contacts_list.html', {'companies': companies})


def add_employee(request, contact_id):
    # Получаем контакт по id
    contact = get_object_or_404(Contact, id=contact_id)

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        position = request.POST.get('position')

        # Создаем нового сотрудника для этого контакта
        Employee.objects.create(
            contact=contact,
            name=name,
            email=email,
            phone=phone,
            position=position
        )

        # Перенаправляем на страницу контактов после добавления
        return redirect('contacts_list')

    return render(request, 'crm/add_employee.html', {'contact': contact})

def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        employee.delete()
        return redirect('contacts_list')


def load_employees(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)
    employees = contact.employees.all()
    return render(request, 'employees.html', {'contact': contact, 'employees': employees})


def add_contact(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        # Получаем данные из формы
        address = request.POST.get('address')
        company_type = request.POST.get('company_type')

        # Создаем новый контакт с адресом и типом компании
        Contact.objects.create(
            company=company,
            address=address,
            company_type=company_type
        )

        # Перенаправляем на страницу компании
        return redirect('company_detail', company_id=company.id)

    return render(request, 'crm/add_contact.html', {'company': company})

def company_main(request):
    companies = Company.objects.all()
    return render(request, 'crm/company_main.html', {'companies': companies})

# DEALS
def deal_list(request):
    # Получаем текущий месяц и год
    print("DEBUG: datetime is", datetime)
    today_date = datetime.today()  # ✅ Теперь работает
    companies = Company.objects.all()
    current_month = today_date.month
    current_year = today_date.year

    # Получаем базовый набор данных
    deals = Deals.objects.all()

    # Фильтруем компании по типу через связанные контакты
    suppliers = Company.objects.filter(contacts__company_type="suppliers").distinct()  # Только поставщики
    buyers = Company.objects.filter(contacts__company_type="buyers").distinct()  # Только покупатели
    hauler = Company.objects.filter(contacts__company_type="hauler").distinct() # Only Haulers

    # Получаем параметры фильтра из запроса
    month = request.GET.get('month', str(current_month).zfill(2))  # Текущий месяц по умолчанию
    year = request.GET.get('year', str(current_year))  # Текущий год по умолчанию

    selected_company_id = request.GET.get('company')

    if selected_company_id:
        deals = deals.filter(
            Q(supplier__id=selected_company_id) |
            Q(buyer__id=selected_company_id) |
            Q(transport_company__id=selected_company_id)
        )

    # Применяем фильтры только если месяц и год указаны
    if month and year:
        deals = deals.filter(date__month=int(month), date__year=int(year))
    elif month:  # Если указан только месяц
        deals = deals.filter(date__month=int(month))
    elif year:  # Если указан только год
        deals = deals.filter(date__year=int(year))

    # Подсчёт итогов по отфильтрованным сделкам
    totals = deals.aggregate(
        total_income_loss=Sum('total_income_loss'),
        total_amount=Sum('total_amount'),
    )

    # Получаем доступные года из базы данных
    years = Deals.objects.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct()

    # Список месяцев для фильтрации (с добавлением пустого значения для "Все")
    months = range(1, 13)  # Месяцы с 1 по 12

    month_names = {
        '01': _('January'),
        '02': _('February'),
        '03': _('March'),
        '04': _('April'),
        '05': _('May'),
        '06': _('June'),
        '07': _('July'),
        '08': _('August'),
        '09': _('September'),
        '10': _('October'),
        '11': _('November'),
        '12': _('December'),
    }

    form = DealForm()

    # Контекст для шаблона
    context = {
        'deals': deals,
        'suppliers': suppliers,  # Только поставщики
        'buyers': buyers,  # Только покупатели, если нужно
        'month': month,
        'year': year,
        'totals': totals,
        'years': sorted(years),  # Сортируем список лет для удобства
        'month_names': month_names,
        'months': months,  # Месяцы для выпадающего списка
        'setting': settings,
        'form': form,
        'hauler': hauler,
        'selected_company_id': int(selected_company_id) if selected_company_id else None,
        'companies': companies,
    }

    # Рендерим страницу с переданным контекстом
    return render(request, 'crm/deal_list.html', context)


from .models import ContactMaterial

def get_price_by_supplier_and_grade(request):
    supplier_id = request.GET.get('supplier_id')
    grade = request.GET.get('grade')

    try:
        contact_material = ContactMaterial.objects.get(contact__company__id=supplier_id, material=grade)
        return JsonResponse({'price': str(contact_material.price)})
    except ContactMaterial.DoesNotExist:
        return JsonResponse({'price': None})


def get_price_by_buyer_and_grade(request):
    buyer_id = request.GET.get('buyer_id')
    grade = request.GET.get('grade')

    try:
        contact_material = ContactMaterial.objects.get(contact__company__id=buyer_id, material=grade)
        return JsonResponse({'price': str(contact_material.price)})
    except ContactMaterial.DoesNotExist:
        return JsonResponse({'price': None})


def export_deals_to_excel(request):
    from openpyxl.utils import get_column_letter
    from openpyxl.styles import Border, Side

    # Получаем текущий месяц и год
    from django.utils.timezone import now

    month = request.GET.get('month')
    year = request.GET.get('year')

    if not month or not year:
        current_date = now()
        month = current_date.month
        year = current_date.year
    else:
        month = int(month)
        year = int(year)

    # Создаем книгу Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Deals"

    # Настройка стилей для заголовков
    header_font = Font(name="Arial", bold=True, color="FFFFFF")  # Белый жирный текст
    header_fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")  # Светло-синий фон
    header_alignment = Alignment(horizontal="center", vertical="center")  # Центрирование текста
    thin_border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))

    # Заголовки столбцов
    headers = [
        'Date', 'Supplier', 'Buyer', 'Grade', 'Shipped Qty', 'Pallets',
        'Received Qty', 'Pallets', 'Supplier Price', 'Supplier Paid Amount', 'Buyer Price',
        'Total Amount', 'Transport Cost', 'Hauler', 'Income/Loss','Scale Ticket'
    ]
    ws.append(headers)

    # Применяем стили к заголовкам
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Получаем сделки только за текущий месяц
    deals = Deals.objects.select_related('supplier', 'buyer').filter(
        date__year=year,
        date__month=month
    )

    # Применяем стили к данным
    data_fill_light = PatternFill(start_color="F8F8F8", end_color="F8F8F8", fill_type="solid")  # Светлый фон для четных строк
    data_fill_dark = PatternFill(start_color="E6E6E6", end_color="E6E6E6", fill_type="solid")  # Темный фон для нечетных строк
    data_font = Font(name="Arial", size=11)  # Стандартный шрифт для данных

    last_row = len(deals) + 1  # Последняя строка данных

    for row_num, deal in enumerate(deals, start=2):
        formatted_date = deal.date.strftime('%d-%b') if deal.date else ''

        grade_value = deal.grade
        if grade_value == 'Baled Cardboard':
            grade_value = 'OCC 11'


        row = [
            formatted_date,
            deal.supplier.name if deal.supplier else '',
            deal.buyer.name if deal.buyer else '',
            grade_value,
            deal.shipped_quantity,
            deal.shipped_pallets,
            deal.received_quantity,
            deal.received_pallets,
            deal.supplier_price,
            deal.supplier_total,
            deal.buyer_price,
            deal.total_amount,
            deal.transport_cost,
            deal.transport_company.name if deal.transport_company else '',
            deal.total_income_loss,
            deal.scale_ticket,
        ]

        ws.append(row)



        # Применяем стили к строке данных
        for col_num, value in enumerate(row, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.font = data_font
            cell.border = thin_border
            cell.fill = data_fill_light if row_num % 2 == 0 else data_fill_dark

    # Начало сводной секции справа от основной таблицы
    summary_col_start = len(headers) + 2  # Первая колонка справа от таблицы
    summary_data = [
        ("TOTAL SALE", "=SUM(L2:L{})".format(len(deals) + 1)),  # Общая продажа (Total Amount)
        ("# of pallets", "=SUM(F2:F{})".format(len(deals) + 1)),  # Общее количество паллет
        ("Transportation cost", "=SUM(M2:M{})".format(len(deals) + 1)),  # Транспортные расходы
        ("Suppliers", "=SUM(J2:J{})".format(len(deals) + 1)),  # Итоги для поставщиков
        ("MT OCC11",
         "=SUMPRODUCT((D2:D{0}=\"OCC11\")+(D2:D{0}=\"OCC 11\")+(D2:D{0}=\"OCC 11 Bale String\")+"
         "(D2:D{0}=\"Loose OCC\")+(D2:D{0}=\"Stock Rolls\")+(D2:D{0}=\"Printers Offcuts\"), E2:E{0})".format(
             last_row
         )),
        ("MT Plastic", "=SUMIF(D2:D{}, \"Flexible Plastic\", E2:E{})".format(last_row, last_row)),
        ("MT Mixed-containers", "=SUMIF(D2:D{}, \"Mixed Container\", E2:E{})".format(last_row, last_row)),
        ("INCOME", "=SUM(O2:O{})".format(last_row))
    ]

    # Заполняем сводные данные
    for row_num, (label, value) in enumerate(summary_data, start=2):
        label_cell = ws.cell(row=row_num, column=summary_col_start)
        label_cell.value = label
        label_cell.font = Font(bold=True, name="Arial", size=12)
        label_cell.alignment = Alignment(horizontal="right")

        value_cell = ws.cell(row=row_num, column=summary_col_start + 1)
        value_cell.value = value
        value_cell.border = thin_border
        value_cell.font = Font(name="Arial", size=11)

    # Автоматическая подгонка ширины столбцов
    for col in ws.columns:
        max_length = 0
        column = get_column_letter(col[0].column)
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        adjusted_width = max_length + 2
        ws.column_dimensions[column].width = adjusted_width

    # Сохраняем файл
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename=deals_{year}_{month}.xlsx'
    wb.save(response)
    return response


def get_deal_details(request, deal_id):
    deal = get_object_or_404(Deals, id=deal_id)

    return JsonResponse({
        'id': deal.id,
        'date': deal.date.strftime('%Y-%m-%d'),

        'supplier_id': deal.supplier.id if deal.supplier else None,
        'supplier_name': deal.supplier.name if deal.supplier else "",

        'buyer_id': deal.buyer.id if deal.buyer else None,
        'buyer_name': deal.buyer.name if deal.buyer else "",

        'grade': deal.grade,
        'shipped_quantity': deal.shipped_quantity,
        'shipped_pallets': deal.shipped_pallets,
        'received_quantity': deal.received_quantity,
        'received_pallets': deal.received_pallets,
        'supplier_price': deal.supplier_price,
        'buyer_price': deal.buyer_price,
        'total_amount': deal.total_amount,

        'transport_cost': deal.transport_cost,
        'transport_company_id': deal.transport_company.id if deal.transport_company else None,
        'transport_company_name': deal.transport_company.name if deal.transport_company else "",

        'scale_ticket': deal.scale_ticket,
    })


@csrf_exempt
def edit_deal(request, deal_id):
    deal = get_object_or_404(Deals, id=deal_id)

    if request.method == 'POST':
        data = json.loads(request.body)

        supplier_id = data.get('supplier')
        buyer_id = data.get('buyer')

        if supplier_id:
            deal.supplier = get_object_or_404(Company, id=supplier_id)
        if buyer_id:
            deal.buyer = get_object_or_404(Company, id=buyer_id)

        # Числовые значения как Decimal
        deal.shipped_quantity = Decimal(data.get('shipped_quantity', deal.shipped_quantity))
        deal.received_quantity = Decimal(data.get('received_quantity', deal.received_quantity))
        deal.buyer_price = Decimal(data.get('buyer_price', deal.buyer_price))
        deal.supplier_price = Decimal(data.get('supplier_price', deal.supplier_price))
        deal.shipped_pallets = Decimal(data.get('shipped_pallets', deal.shipped_pallets))
        deal.received_pallets = Decimal(data.get('received_pallets', deal.received_pallets))
        deal.transport_cost = Decimal(data.get('transport_cost', deal.transport_cost))

        # Остальные поля
        deal.date = data.get('date', deal.date)
        deal.grade = data.get('grade', deal.grade)

        transport_company_id = data.get('transport_company')
        if transport_company_id:
            deal.transport_company = get_object_or_404(Company, id=transport_company_id)

        deal.scale_ticket = data.get('scale_ticket', deal.scale_ticket)

        # Итоговые расчёты
        deal.total_amount = deal.shipped_quantity * deal.buyer_price
        deal.supplier_total = deal.received_quantity * deal.supplier_price
        deal.total_income_loss = deal.total_amount - (deal.supplier_total + deal.transport_cost)

        deal.save()

        return JsonResponse({
            'status': 'success',
            'deal': {
                'id': deal.id,
                'date': deal.date,
                'supplier': deal.supplier.name,
                'buyer': deal.buyer.name if deal.buyer else '',
                'grade': deal.grade,
                'total_amount': str(deal.total_amount),
                'total_income_loss': str(deal.total_income_loss),
                'scale_ticket': deal.scale_ticket
            }
        })

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def delete_deal(request, deal_id):
    if request.method == 'DELETE':
        deal = get_object_or_404(Deals, id=deal_id)
        deal.delete()
        return JsonResponse({'message': 'Deal deleted successfully!'})
    return HttpResponse(status=405)  # Method not allowed


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
        serializer = DealSerializer(data=request.data)
        if serializer.is_valid():
            scale_ticket = request.data.get("scale_ticket")  # ✅ Берем scale_ticket

            # ✅ Создаем объект, передавая scale_ticket
            deal = serializer.save(scale_ticket=scale_ticket)

            return Response(DealSerializer(deal).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deals.objects.all()
    serializer_class = DealSerializer


def get_licence_plates(request):
    plates = [
        'SY1341',
        'WB3291',
        '153'
    ]
    return JsonResponse({"plates": plates})


SCALE_TICKET_COUNTER_FILE = os.path.join(settings.BASE_DIR, 'scale_ticket_counter.json')



@csrf_exempt
def get_scale_ticket_counters(request):


    if request.method == 'GET':
        if not os.path.exists(SCALE_TICKET_COUNTER_FILE):
            with open(SCALE_TICKET_COUNTER_FILE, 'w') as f:
                json.dump({"scale_ticket": 108346}, f)


        with open(SCALE_TICKET_COUNTER_FILE, 'r') as f:
            data = json.load(f)
        return JsonResponse(data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def increment_scale_ticket_counters(request):
    if request.method == 'POST':
        # ✅ Если файл не существует, создаём его с начальными значениями
        if not os.path.exists(SCALE_TICKET_COUNTER_FILE):
            with open(SCALE_TICKET_COUNTER_FILE, 'w') as f:
                json.dump({"bol": 1000, "load": 2000}, f)

        # ✅ Читаем и обновляем
        with open(SCALE_TICKET_COUNTER_FILE, 'r+') as f:
            data = json.load(f)
            data["scale_ticket"] += 1
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        return JsonResponse({"status": "updated", "scale_ticket": data["scale_ticket"]})
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)




def sales_analytics(request):
    from django.db.models import Sum, Q
    from django.db.models.functions import ExtractMonth, ExtractYear
    from django.http import JsonResponse, HttpResponseRedirect
    from datetime import datetime

    # Получаем текущий месяц и год
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Получаем параметры фильтра из запроса
    month = request.GET.get('month', str(current_month).zfill(2))  # По умолчанию текущий месяц
    year = request.GET.get('year', str(current_year))               # По умолчанию текущий год

    # --- Данные для графика по месяцам (фильтрация только по году) ---
    deals_year = Deals.objects.filter(date__year=int(year))
    monthly_data = deals_year.values(month=ExtractMonth('date')).annotate(
        total_income=Sum('total_income_loss'),
        total_pallets=Sum('shipped_pallets'),
        transport_cost=Sum('transport_cost'),
        supplier_total=Sum('supplier_total'),
        total_tonnage=Sum('shipped_quantity'),
        occ11_tonnage=Sum(
            'shipped_quantity',
            filter=(
                    Q(grade="OCC11") |
                    Q(grade="OCC 11") |
                    Q(grade="OCC 11 Bale String") |
                    Q(grade="Loose OCC") |
                    Q(grade="Printers Offcuts") |
                    Q(grade="Stock Rolls") |
                    Q(grade="Cardboard Stock Lots") |
                    Q(grade="DLK") |
                    Q(grade='Baled Cardboard')
            )
        ),

        plastic_tonnage=Sum('received_quantity', filter=Q(grade="Flexible Plastic")),
            mixed_tonnage=Sum('received_quantity', filter=Q(grade="Mixed Container")),
            total_sales=Sum('total_amount')
        ).order_by('month')

    chart_data = {
        'months': [entry['month'] for entry in monthly_data],
        'profit': [float(entry["total_income"] or 0) for entry in monthly_data],
        'pallets': [float(entry['total_pallets'] or 0) for entry in monthly_data],
        'hauler': [float(entry['transport_cost'] or 0) for entry in monthly_data],
        'suppliers': [float(entry["supplier_total"] or 0) for entry in monthly_data],
        'total_tonnage': [float(entry["total_tonnage"] or 0) for entry in monthly_data],
        'occ11_tonnage': [float(entry["occ11_tonnage"] or 0) for entry in monthly_data],
        'plastic_tonnage': [float(entry["plastic_tonnage"] or 0) for entry in monthly_data],
        'mixed_tonnage': [float(entry["mixed_tonnage"] or 0) for entry in monthly_data],
        'sales': [float(entry["total_sales"] or 0) for entry in monthly_data]
    }

    # Если запрос AJAX, возвращаем данные графика в JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(chart_data)

    # --- Данные для остальных статистик (фильтрация по месяцу и году) ---
    deals_details = Deals.objects.all()
    if month and year:
        deals_details = deals_details.filter(date__month=int(month), date__year=int(year))
    elif month:
        deals_details = deals_details.filter(date__month=int(month))
    elif year:
        deals_details = deals_details.filter(date__year=int(year))

    suppliers_income = deals_details.values('supplier').annotate(total_income_loss=Sum('total_income_loss'))
    suppliers_income_dict = {
        contact.company.name: float(entry['total_income_loss'] or 0)
        for entry in suppliers_income
        for contact in Contact.objects.filter(company__id=entry['supplier'])
    }

    occ11_filter = Q(grade__iexact="OCC11") | Q(grade__iexact="OCC 11") | Q(grade__iexact="Loose OCC") | \
                   Q(grade__iexact="OCC 11 Bale String") | Q(grade__iexact="Printers Offcuts") | Q(
        grade__iexact="Stock Rolls")

    total_deals = deals_details.count()
    total_sale = deals_details.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_pallets = deals_details.aggregate(Sum('shipped_pallets'))['shipped_pallets__sum'] or 0
    transportation_fee = deals_details.aggregate(Sum('transport_cost'))['transport_cost__sum'] or 0
    suppliers_total = deals_details.aggregate(Sum('supplier_total'))['supplier_total__sum'] or 0
    mt_occ11 = deals_details.filter(occ11_filter).aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    mt_plastic = deals_details.filter(grade="Flexible Plastic").aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    mt_mixed_containers = deals_details.filter(grade="Mixed Container").aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    income = deals_details.aggregate(Sum('total_income_loss'))['total_income_loss__sum'] or 0

    company_pallets = CompanyPallets.objects.select_related('company_name')

    # Обработка формы обновления паллет
    if request.method == 'POST' and 'update_pallets' in request.POST:
        for pallet in company_pallets:
            new_pallet_count = request.POST.get(f"pallets_{pallet.id}")
            new_cages_count = request.POST.get(f"cages_{pallet.id}")  # Получаем данные клеток
            new_bags_count = request.POST.get(f"bags_{pallet.id}")

            if new_pallet_count is not None:
                pallet.pallets_count = int(new_pallet_count)
            if new_cages_count is not None:
                pallet.cages_count = int(new_cages_count)

            if new_bags_count is not None:
                pallet.bags_count = int(new_bags_count)

            pallet.save()
        return HttpResponseRedirect(request.path)

    years = Deals.objects.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct()
    months = range(1, 13)

    # Объединяем все данные в один context
    context = {
        'chart_data': chart_data,
        'year': year,
        'suppliers_income': suppliers_income_dict,
        'total_deals': total_deals,
        'total_sale': total_sale,
        'total_pallets': total_pallets,
        'transportation_fee': transportation_fee,
        'suppliers_total': suppliers_total,
        'mt_occ11': mt_occ11,
        'mt_plastic': mt_plastic,
        'mt_mixed_containers': mt_mixed_containers,
        'income': income,
        'company_pallets': company_pallets,
        'month': month,
        'years': sorted(years),
        'months': months,
    }

    return render(request, 'crm/sales_analytics.html', context)


    # Получаем доступные года и месяцы
    years = Deals.objects.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct()
    months = range(1, 13)

    context = {
        'suppliers_income': suppliers_income_dict,
        'total_deals': total_deals,
        'total_sale': total_sale,
        'total_pallets': total_pallets,
        'transportation_fee': transportation_fee,
        'suppliers_total': suppliers_total,
        'mt_occ11': mt_occ11,
        'mt_plastic': mt_plastic,
        'mt_mixed_containers': mt_mixed_containers,
        'income': income,
        'company_pallets': company_pallets,
        'month': month,
        'year': year,
        'years': sorted(years),
        'months': months,
    }



def add_contact_material(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)

    if request.method == 'POST':
        # Создаем экземпляр формы с данными из POST-запроса
        form = ContactMaterialForm(request.POST, request.FILES)

        # Проверяем, что форма валидна
        if form.is_valid():
            # Если форма валидна, сохраняем материал
            contact_material = form.save(commit=False)
            contact_material.contact = contact  # Связываем материал с контактом
            contact_material.save()

            # После сохранения редиректим на страницу с контактами
            return redirect('view_contact', id = contact.id)

    else:
        # Если метод запроса GET, создаем пустую форму
        form = ContactMaterialForm()

    # Рендерим шаблон с формой и данными о контакте
    return render(request, 'crm/add_contact_material.html', {'form': form, 'contact': contact})


def edit_contact_material(request, pk):
    contact_material = get_object_or_404(ContactMaterial, pk=pk)

    if request.method == 'POST':
        form = ContactMaterialForm(request.POST, instance=contact_material)
        if form.is_valid():
            form.save()
            return redirect('view_contact', id=contact_material.contact.id)
    else:
        form = ContactMaterialForm(instance=contact_material)

    return render(request, 'crm/edit_contact_material.html', {'form': form, 'contact_material': contact_material})


#REPORTS

def report_list(request):
    return render(request, 'crm/report_list.html')


def company_report(request):
    # Получаем текущий месяц и год
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Получаем параметры фильтра из запроса
    selected_company_id = request.GET.get('company', '')
    month = request.GET.get('month', '') or str(current_month).zfill(2)
    year = request.GET.get('year', '') or str(current_year)

    # Фильтрация сделок
    deals = Deals.objects.all()

    if selected_company_id:
        # Фильтруем по поставщикам и покупателям
        deals = deals.filter(Q(supplier__id=int(selected_company_id)))

    if month and year:
        deals = deals.filter(date__month=int(month), date__year=int(year))
    elif month:  # Если указан только месяц
        deals = deals.filter(date__month=int(month))
    elif year:  # Если указан только год
        deals = deals.filter(date__year=int(year))

    # Итоги
    total_amount_supplier = deals.aggregate(Sum('supplier_total'))['supplier_total__sum'] or 0


    # Список компаний для выбора в фильтре
    companies = Company.objects.filter(contacts__company_type='suppliers').distinct()

    # Получаем доступные года из базы данных для фильтрации
    years = Deals.objects.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct()

    # Список месяцев для фильтрации
    months = range(1, 13)  # Месяцы с 1 по 12

    # Контекст для шаблона
    context = {
        'deals': deals,
        'total_amount_supplier': total_amount_supplier,
        'companies': companies,
        'selected_company_id': int(selected_company_id) if selected_company_id.isdigit() else None,
        'month': month,
        'year': year,
        'years': sorted(years),  # Сортируем список лет для удобства
        'months': months,  # Месяцы для выпадающего списка
    }
    return render(request, 'crm/company_report.html', context)



def export_company_report_pdf(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    import os
    from django.conf import settings
    from django.utils.text import slugify


    # Получение фильтров из запроса
    selected_company_id = request.GET.get('company', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')

    # Текущая дата для отчета
    now = datetime.now()

    # Получение всех сделок
    deals = Deals.objects.all()
    if selected_company_id:
        deals = deals.filter(supplier__id=int(selected_company_id))
    if month:
        deals = deals.filter(date__month=int(month))
    if year:
        deals = deals.filter(date__year=int(year))

    first_deal = deals.first()


    # Данные для таблицы
    data = [["Date", "Grade", "Net", "Price", "Amount", "Scale Ticket"]]
    for deal in deals:
        data.append([
            deal.date.strftime("%Y-%m-%d"),
            deal.grade,
            f"{deal.received_quantity:.4f}",
            f"${deal.supplier_price:.2f}",
            f"${deal.supplier_total:.2f}",
            deal.scale_ticket
        ])

    # Итоги
    total_net = sum([deal.received_quantity for deal in deals])
    total_amount = sum([deal.supplier_total for deal in deals])

    # Создание PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    current_y = height - 50

    logo_path = os.path.join(settings.BASE_DIR, 'crm', 'static', 'crm', 'images', 'cl2.png')
    if os.path.exists(logo_path):
        pdf.drawImage(ImageReader(logo_path), 30, current_y - 40, width=50, height=50, mask='auto')

    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.darkblue)
    pdf.drawRightString(width - 30, current_y - 10, "Local to Global Recycling Inc.")
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.black)
    pdf.drawRightString(width - 30, current_y - 23, "19090 Lougheed Hwy.")
    pdf.drawRightString(width - 30, current_y - 33, "Pitt Meadows, BC V3Y 2M6")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, current_y - 10, "Shipment Summary")

    # 📍 Customer info
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, height - 160, "Customer:")

    customer_details1 = []
    if first_deal and first_deal.supplier:
        customer_details1.append(first_deal.supplier.name)
        contact = first_deal.supplier.contacts.filter(address__isnull=False).first()
        if contact and contact.address:
            customer_details1.extend(contact.address.strip().split('\n'))
        else:
            customer_details1.append("Address not available")
    else:
        customer_details1 = ["Unknown"]

    pdf.setFont("Helvetica", 10)
    y_position = height - 175
    for line in customer_details1:
        pdf.drawString(85, y_position, line.strip())
        y_position -= 15

    # 📊 Таблица под адресом клиента + небольшой отступ
    table_top_y = y_position - 20
    table = Table(data, colWidths=[80, 140, 60, 80, 80,80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    # Определим высоту таблицы для расчёта позиции итогов
    table_width, table_height = table.wrap(0, 0)
    table.drawOn(pdf, 30, table_top_y - table_height)

    # 📉 Итоги ниже таблицы
    summary_y = table_top_y - table_height - 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, summary_y, f"Total Net: {total_net:.2f} MT")
    pdf.drawString(30, summary_y - 20, f"Total Amount: ${total_amount:.2f}")


    # 📊 Расчёт итогов по каждому грейду
    pdf.setFont("Helvetica", 10)
    grade_summary = {}

    for deal in deals:
        key = (deal.grade, deal.supplier_price)
        if key not in grade_summary:
            grade_summary[key] = {"amount": 0, "net": 0}
        grade_summary[key]["net"] += deal.received_quantity
        grade_summary[key]["amount"] += deal.supplier_total

    y = summary_y - 50  # ⬇ Начинаем ниже итогов

    for (grade, price), values in grade_summary.items():
        amount = values["amount"]
        net = values["net"]
        pdf.drawString(30, y, f"{grade} (${price:.2f}) – {net:.2f} MT – ${amount:.2f} ")
        y -= 15  # отступ между строками

    # 📁 Название файла
    raw_name = first_deal.supplier.name if first_deal and first_deal.supplier else "Unknown"
    safe_name = slugify(raw_name)
    month_str = datetime.strptime(month, "%m").strftime("%b") if month else now.strftime("%b")
    year_str = year if year else now.strftime("%Y")
    filename = f"L2G_{safe_name}_Supply_List_{month_str}_{year_str}.pdf"

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response




def get_deal_by_ticket(request):
    ticket_number = request.GET.get('ticket_number', None)
    print(f"Получен запрос на поиск Scale Ticket: {ticket_number}")

    if not ticket_number:
        return JsonResponse({'success': False, 'error': 'No ticket number provided'})

    try:
        deal = Deals.objects.filter(scale_ticket=ticket_number).first()
        if not deal:
            print("Ошибка: Сделка не найдена")
            return JsonResponse({'success': False, 'error': 'No deal found for this ticket number'}, status=404)

        print(f"Найдена сделка: {deal}")

        return JsonResponse({
            'success': True,
            'deal': {
                'id': deal.id,
                'date': deal.date.strftime('%Y-%m-%d'),
                'received_quantity': float(deal.received_quantity),
                'received_pallets': deal.received_pallets,
                'supplier_name': deal.supplier.name if deal.supplier else "",
                'grade': deal.grade,
            }
        })
    except Exception as e:
        import traceback
        print("Ошибка сервера:", traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




def export_scale_ticket_pdf(request):
    ticket_number = request.GET.get('ticket_number', None)

    if not ticket_number:
        return HttpResponse("⚠️ No ticket number provided.", status=400)

    # Получаем **все** сделки с таким scale_ticket
    deals = Deals.objects.filter(scale_ticket=ticket_number)

    if not deals.exists():
        return HttpResponse("⚠️ No deals found for this ticket number.", status=404)

    first_deal = deals.first()

    # 📌 Считаем общий вес материалов и паллет
    total_material_weight = sum(deal.received_quantity * 1000 for deal in deals)  # В кг
    total_pallets_weight = sum(deal.received_pallets * 15 for deal in deals if deal.received_pallets)

    # 📌 Получаем данные из формы (если переданы)
    licence_plate = request.GET.get('licence_plate', "N/A")
    tare_weight = float(request.GET.get('tare_weight', 5170))  # 🚛 Базовый вес
    net_weight = float(total_material_weight) + float(total_pallets_weight)  # 📦 Итоговый net_weight
    gross_weight = float(tare_weight) + float(net_weight)  # 📌 Gross = Tare + Net

    # 📌 Форматируем числа
    gross_weight_str = f"{gross_weight:.1f} KG"
    tare_weight_str = f"{tare_weight:.1f} KG"
    net_weight_str = f"{net_weight:.1f} KG"

    # 🕒 Время (из формы или по умолчанию)
    deal_time = request.GET.get('time', "N/A")

    # 🖨 Лог для отладки весов
    print(f"📊 Scale Ticket #{ticket_number} | Gross: {gross_weight}, Tare: {tare_weight}, Net: {net_weight}")

    # Создаём PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # 🏢 Логотип
    logo_path = os.path.join(settings.BASE_DIR, 'crm', 'static', 'crm', 'images', 'company_logo.png')

    if os.path.exists(logo_path):
        pdf.drawImage(ImageReader(logo_path), 40, height - 80, width=70, height=50, mask='auto')
        print(f"✅ Логотип найден: {logo_path}")
    else:
        print(f"🚨 Логотип НЕ найден: {logo_path}")

    # 📌 Название компании
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.darkblue)
    pdf.drawString(130, height - 45, "Local to Global Recycling Inc.")

    # 📍 Адрес
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.black)
    pdf.drawString(130, height - 55, "19090 Lougheed Hwy.")
    pdf.drawString(130, height - 65, "Pitt Meadows, BC V3Y 2M6")

    # 🏷 Заголовок Scale Ticket
    pdf.setFont("Helvetica", 12)
    pdf.drawString(80, height - 110, f"Scale Ticket #: {ticket_number}")

    # 📆 Дата и время
    pdf.setFont("Helvetica", 10)
    pdf.drawString(80, height - 130, f"Date: {first_deal.date.strftime('%Y-%m-%d')}")
    pdf.drawString(80, height - 150, f"Time: {deal_time}")
    pdf.drawString(80, height - 170, f"Customer:")

    # 👤 Customer details (с переносами строк)
    customer_details = [first_deal.supplier.name] if first_deal.supplier else ["Unknown"]
    y_position = height - 190  # Опускаем ниже заголовка "Customer:"
    for line in customer_details:
        pdf.drawString(85, y_position, line.strip())
        y_position -= 15  # Отступ вниз

    # 📋 Данные справа
    pdf.drawString(350, height - 110, f"Licence: {licence_plate}")
    pdf.drawString(350, height - 130, f"Gross: {gross_weight_str}")
    pdf.drawString(350, height - 150, f"Tare: {tare_weight_str}")
    pdf.drawString(350, height - 170, f"Net: {net_weight_str}")
    pdf.drawString(350, height - 190, f"Pallets #: {first_deal.received_pallets}")

    # 📌 Позиция таблицы (ниже)
    y_position = height - 320

    # 📊 Данные таблицы
    data = [['MATERIAL', 'WEIGHT (KG)', 'PRICE ($/KG)', 'AMOUNT']]
    total_amount = 0

    for deal in deals:
        received_kg = deal.received_quantity * 1000
        sup_price = deal.supplier_price / 1000  # ✅ Цена за кг
        amount = received_kg * sup_price
        total_amount += amount

        data.append([deal.grade, f"{received_kg:.1f}", f"${sup_price:.2f}", f"${amount:.2f}"])

    # 🏋 Добавляем вес паллет, если есть
    if total_pallets_weight > 0:
        data.append(['Pallets', f"{total_pallets_weight:.1f}", '', ''])

    # 📑 Создаем таблицу
    table = Table(data, colWidths=[200, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
    ]))

    # 🖨 Вывод таблицы в PDF
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 80, y_position)

    # 💰 Итоговая сумма
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(80, y_position - 25, f"Total: ${total_amount:.2f}")

    # 🗂 Структура директорий
    today = datetime.today()
    year = today.strftime("%Y")
    month = today.strftime("%B")  # April, May и т.д.
    raw_supplier_name = first_deal.supplier.name if first_deal.supplier else "Unknown Supplier"

    print(f"📌 Supplier name в PDF: {raw_supplier_name}")

    supplier_name = sanitize_filename(raw_supplier_name)

    # 📂 Путь сохранения
    directory = os.path.join(settings.MEDIA_ROOT, "reports", "scale_tickets", supplier_name, year, month)
    os.makedirs(directory, exist_ok=True)

    # 📝 Название файла
    filename = f"Ticket {ticket_number}.pdf"
    filepath = os.path.join(directory, filename)

    # ✅ Завершаем PDF и перематываем буфер
    pdf.save()
    buffer.seek(0)

    # 💾 Сохраняем PDF в файл
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())

    print(f"✅ PDF сохранён в: {filepath}")

    # 📤 Возвращаем как ответ пользователю
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Ticket {ticket_number}.pdf"'
    return response

# Область доступа
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "c_id.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


from .models import SCaleTicketStatus  # ← используй как названо у тебя

def scale_ticket_browser(request):
    relative_path = request.GET.get('path', '').strip('/')

    base_dir = os.path.join(settings.MEDIA_ROOT, 'reports', 'scale_tickets')
    abs_path = os.path.join(base_dir, relative_path)

    if not os.path.exists(abs_path):
        return HttpResponse("❌ Path not found", status=404)

    folders = []
    files = []

    for entry in sorted(os.listdir(abs_path)):
        full_entry = os.path.join(abs_path, entry)
        if os.path.isdir(full_entry):
            folders.append(entry)
        elif entry.lower().endswith('.pdf'):
            files.append(entry)

    if relative_path:
        path_parts = relative_path.split('/')
        back_path = '/'.join(path_parts[:-1])
    else:
        back_path = None

    # ✅ Статусы
    file_statuses = {
        s.file_path.strip().replace('\\', '/'): True
        for s in SCaleTicketStatus.objects.filter(sent=True)
    }

    context = {
        'relative_path': relative_path,
        'folders': folders,
        'files': files,
        'back_path': back_path,
        'file_statuses': file_statuses,
    }


    return render(request, 'crm/scale_ticket_browser.html', context)

from django.core.mail import EmailMessage

@csrf_exempt
def send_scale_ticket_email(request):
    import json
    from django.utils.timezone import now

    if request.method == 'POST':
        data = json.loads(request.body)
        relative_path = data.get('path')
        recipient_email = data.get('email')  # в будущем можно сделать автоопределение

        abs_path = os.path.join(settings.MEDIA_ROOT, 'reports', 'scale_tickets', relative_path)
        if not os.path.exists(abs_path):
            return JsonResponse({'error': 'File not found'}, status=404)

        try:
            email = EmailMessage(
                subject="📎 Scale Ticket",
                body="Attached scale ticket file.",
                from_email=settings.EMAIL_HOST_USER,
                to=[recipient_email],
            )
            email.attach_file(abs_path)
            email.send()

            status, created = SCaleTicketStatus.objects.get_or_create(file_path=relative_path)
            status.sent = True
            status.sent_at = now()
            status.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# ID календаря
CALENDAR_ID = "dmitry@wastepaperbrokers.com"

def get_calendar_events():
    """Получает события из Google Calendar."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8081, access_type="offline", prompt="consent")
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        except Exception as e:
            return {"error": f"Ошибка авторизации: {str(e)}"}

    try:
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(t.utc).replace(microsecond=0).isoformat() + "Z"

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
    except Exception as e:
        return {"error": f"Ошибка загрузки событий: {str(e)}"}

    return events

def task_list(request):
    suppliers = Company.objects.filter(contacts__company_type="suppliers")
    buyers = Company.objects.filter(contacts__company_type="buyers")
    generate_recurring_shipments()

    context = {
        'suppliers': suppliers,
        'buyers': buyers,
        'materials_list': settings.MATERIALS_LIST,  # ✅ Передаем MATERIALS_LIST правильно
    }
    return render(request, 'crm/task_list.html', context)


def get_events(request):
    """Возвращает события в формате JSON для FullCalendar"""
    events = Event.objects.all()
    event_list = [
        {
            "id": event.id,
            "title": event.title,
            "start": event.start.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": event.end.strftime("%Y-%m-%dT%H:%M:%S") if event.end else None,
            "allDay": event.all_day,
        }
        for event in events
    ]
    return JsonResponse(event_list, safe=False)

@csrf_exempt
def add_event(request):
    """Добавляет новое событие в календарь"""
    try:
        data = json.loads(request.body)
        title = data.get("title")
        start = data.get("start")

        if not title or not start:
            return JsonResponse({"error": "title и start обязательны"}, status=400)

        # ✅ Преобразуем дату
        start_datetime = datetime.fromisoformat(start)

        # ✅ Проверяем, есть ли уже таймзона, если нет — добавляем
        if start_datetime.tzinfo is None:
            start_datetime = timezone.make_aware(start_datetime)

        # ✅ Создаем событие в БД
        event = Event.objects.create(
            title=title,
            start=start_datetime,
            all_day=False
        )

        return JsonResponse({"status": "success", "event": {
            "id": event.id,
            "title": event.title,
            "start": event.start.isoformat(),
            "allDay": event.all_day
        }})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




@csrf_exempt
def delete_event(request, event_id):
    """Удаляет событие"""
    if request.method == "DELETE":
        event = Event.objects.filter(id=event_id).first()
        if event:
            event.delete()
            return JsonResponse({"status": "deleted"})
        return JsonResponse({"error": "Event not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)



def get_grades(request):
    """
    Возвращает список всех материалов (грейдов).
    """
    return JsonResponse(list(settings.MATERIALS_LIST.keys()), safe=False)


@csrf_exempt
def add_scheduled_shipment(request):
    """
    Добавляет новую запланированную отгрузку.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            supplier = Company.objects.get(id=data["supplier"])
            buyer = Company.objects.get(id=data["buyer"])

            # 🔹 Извлекаем дату и время
            date_part = data["datetime"].split("T")[0]
            time_part = data["datetime"].split("T")[1]

            # 🔹 Флаги повтора
            is_recurring = data.get("is_recurring", False)
            recurrence_type = data.get("recurrence_type", None)
            recurrence_day = data.get("recurrence_day", None)

            shipment = ScheduledShipment.objects.create(
                supplier=supplier,
                buyer=buyer,
                date=data["datetime"].split("T")[0],
                time=data["datetime"].split("T")[1],
                grade=data["grade"],
                is_recurring=data.get("is_recurring", False),
                recurrence_type=data.get("recurrence_type", None),
                recurrence_day=data.get("recurrence_day", None)
            )

            return JsonResponse({"status": "success", "shipment_id": shipment.id})
        except Company.DoesNotExist:
            return JsonResponse({"error": "Supplier or Buyer not found"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_scheduled_shipments(request):
    """
    Возвращает список всех запланированных отгрузок.
    """
    shipments = ScheduledShipment.objects.filter(is_done=False).order_by("date")
    shipment_list = [
        {
            "id": shipment.id,
            "date": shipment.date.strftime("%Y-%m-%d"),
            "time": shipment.time.strftime("%H:%M"),
            "supplier": shipment.supplier.name,
            "buyer": shipment.buyer.name,
            "grade": shipment.grade
        }
        for shipment in shipments
    ]
    return JsonResponse(shipment_list, safe=False)

@csrf_exempt
def delete_scheduled_shipment(request, shipment_id):
    """
    Удаляет запланированную отгрузку.
    """
    if request.method == "DELETE":
        try:
            shipment = ScheduledShipment.objects.get(id=shipment_id)
            shipment.delete()
            return JsonResponse({"status": "deleted"})
        except ScheduledShipment.DoesNotExist:
            return JsonResponse({"error": "Shipment not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)



from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


@csrf_exempt
def generate_bol_pdf(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        spacing = 15
        y = height - 50

        # 📦 Логотип и название компании
        logo_path = os.path.join(settings.BASE_DIR, 'crm', 'static', 'crm', 'images', 'company_logo.png')
        if os.path.exists(logo_path):
            p.drawImage(ImageReader(logo_path), 40, height - 75, width=70, height=50, mask='auto')

        # 🏢 Название компании и адрес справа
        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(colors.darkblue)
        p.drawRightString(width - 40, height - 45, "Local to Global Recycling Inc.")

        p.setFont("Helvetica", 8)
        p.setFillColor(colors.black)
        p.drawRightString(width - 40, height - 58, "19090 Lougheed Hwy.")
        p.drawRightString(width - 40, height - 68, "Pitt Meadows, BC V3Y 2M6")

        # 🧾 Заголовок по центру
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width / 2, height - 45, "BILL OF LADING")

        # 🔹 BOL Number под заголовком (с отступом вниз)
        bol_number = data.get("bolNumber", "BOL-00000")
        p.setFont("Helvetica-Bold", 12)
        p.drawCentredString(width / 2, height - 65, f"{bol_number}")

        # 📋 Основная информация
        info_y = height - 280
        p.setFont("Helvetica", 10)

        def draw_line(label, value):
            nonlocal y
            p.drawString(40, y, f"{label}: {value}")
            y -= spacing

        freight = data.get("freightTerms", "").strip().lower()
        checkbox_line = (
            "Freight Charge Terms:\n"
            "(freight charges are prepaid unless marked otherwise)\n\n"
        
            f"Prepaid {'✓' if freight == 'prepaid' else ''}________     "
            f"Collect {'✓' if freight == 'collect' else ''}________     "
            f"3rd Party {'✓' if freight == '3rd party' else ''}________"
        )

        shipping_info = (
            f"Ship Date: {data.get('shipDate', '')}    Due Date: {data.get('dueDate', '')}\n"
            f"Carrier: {data.get('carrier', '')}\n"
            f"PO Number: {data.get('poNumber', '')}"
        )

        supp_info = (
            f"{data.get('shipFrom', '')}\n"
            f"{data.get('shipFromAddress', '')}\n"

        )

        buyer_info = (
            f"{data.get('shipTo', '')}\n"
            f"{data.get('shipToAddress', '')}\n"

        )

        references_info = (
            f"BOL # {data.get('bolNumber', '')}\n"
            f"Load # {data.get('loadNumber', '')}\n"
            f"PO Number: {data.get('poNumber', '')}"
        )

        styles = getSampleStyleSheet()

        info_data = [
            ["SHIP FROM", ""],
            [supp_info, shipping_info],
            ["SHIP TO","REFERENCES"],
            [buyer_info,references_info],
            ["THIRD PARTY FREIGHT CHARGES BILL TO: ", "FREIGHT CHARGE  TERMS: "],
            ["", checkbox_line],

        ]

        info_col_widths = [285, 285]
        info_table_width = sum(info_col_widths)
        x_info = (width - info_table_width) / 2  # Центрируем по ширине страницы

        info_table = Table(info_data, colWidths=info_col_widths)
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # SHIP FROM
            ('BACKGROUND', (0, 2), (-1, 2), colors.lightgrey),  # SHIP TO / REFERENCES
            ('BACKGROUND', (0, 4), (-1, 4), colors.lightgrey),  # THIRD PARTY / TERMS (если хочешь)

            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.black),
            ('TEXTCOLOR', (0, 4), (-1, 4), colors.black),

            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        ]))
        info_table.wrapOn(p, width, height)
        info_table.drawOn(p, x_info, info_y)


        # 📦 Таблица товаров
        y = info_y - info_table._height + 120

        col_widths = [50, 60, 60, 50, 35, 170, 60, 40, 40]
        table_width = sum(col_widths)

        headers = ["QTY", "Handling", "PKG", "WT", "HM", "COMMODITY DESCRIPTION", "DIMS", "CLASS", "NMFC"]
        commodities = data.get('commodities', [])
        table_data = [headers]
        total_weight = 0

        for item in commodities:
            wt = float(item.get("weight", 0) or 0)
            total_weight += wt
            row = [
                item.get("qty", ""),
                item.get("handling", ""),
                item.get("pkg", ""),
                wt,
                item.get("hm", ""),
                item.get("description", ""),
                item.get("dims", ""),
                item.get("class", ""),
                item.get("nmfc", "")
            ]
            table_data.append(row)

        # 👉 добавляем строку TOTAL
        table_data.append(['', '', '', f"{total_weight:.1f}", '', 'TOTAL', '', '', ''])
        num_rows = len(table_data)

        # 👉 создаём таблицу
        commodity_table = Table(table_data, colWidths=col_widths)
        commodity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # заголовки
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, 0), 0.5, colors.black),

            ('BOX', (0, 1), (-1, -1), 0.5, colors.black),  # внешняя рамка
            ('INNERGRID', (0, 1), (-1, -1), 0, colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),

            # 👉 строка TOTAL — жирная и серая
            ('BACKGROUND', (0, num_rows - 1), (-1, num_rows - 1), colors.lightgrey),
            ('FONTNAME', (0, num_rows - 1), (-1, num_rows - 1), 'Helvetica-Bold'),
            ('GRID', (0, num_rows - 1), (-1, num_rows - 1), 0.5, colors.black),
        ]))

        # 👉 позиционирование по центру страницы
        x = (width - table_width) / 2  # это ключ!
        commodity_table.wrapOn(p, width, height)
        commodity_table.drawOn(p, x, y)

    # 📦 Таблица состояния загрузки
    coll_widths = [370, 100, 100]
    table3_width = sum(coll_widths)

    # ✅ Данные чекбоксов
    trailer_loaded = data.get('trailer_loaded', '').strip().lower()
    freight_counted = data.get('freight_counted', '').strip().lower()

    # ✅ Текст с галочками
    check_trailer_load = (
        f"Trailer Loaded:\n\n"
        f"By Shipper {'✓' if trailer_loaded == 'shipper' else ''} ____\n"
        f"By Driver  {'✓' if trailer_loaded == 'driver' else ''} ____"
    )

    check_freight_counted = (
        f"Freight Counted:\n\n"
        f"By Shipper {'✓' if freight_counted == 'shipper' else ''} ____\n"
        f"By Driver  {'✓' if freight_counted == 'driver' else ''} ____"
    )

    # ✅ Заголовки и данные
    table3_data = [
        ["", "TRAILER LOADED", "FREIGHT COUNTED"],
        ["", check_trailer_load, check_freight_counted]
    ]

    # 👉 создаём таблицу
    load_table = Table(table3_data, colWidths=coll_widths)
    load_table.setStyle(TableStyle([
        ('BACKGROUND', (1, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))

    # 📌 Позиция для новой таблицы (ниже)
    y2 = y - commodity_table._height - 30  # отступ вниз
    x2 = (width - table3_width) / 2

    load_table.wrapOn(p, width, height)
    load_table.drawOn(p, x2, y2)

    # Подписи слева
    shipper1 = (
        "Shipper Signature/Date\n\n"
        "Shipper: ____________________     Date: _______________"
    )

    carrier1 = (
        "Carrier Signature/Pickup Date\n\n"
        "Carrier: ____________________     Date: _______________"
    )

    signarure2 = (

        "Receiver Signature: ________________________________\n\n"
        "Print Name: ________________________________________\n\n"
        "Exceptions: _________________________________________\n\n"
        "_____________________________________________________\n"
    )

    # 🔹 Содержимое под Pickup
    pickup_table = (
        "                Time             Shipper\n"
        "                                     Initials\n"
        "       Appt: _____           _______\n"
        "   Time In: _____           _______\n"
        "Time Out: _____           _______\n"
    )

    delivery_table = (
        "                Time             Receiver\n"
        "                                     Initials\n"
        "       Appt: _____           _______\n"
        "   Time In: _____           _______\n"
        "Time Out: _____           _______\n"
    )
    # Табличные данные
    signature_data = [
        [shipper1, carrier1],  # 1 строка: 2 графы + пустая

    ]

    # Ширины колонок — при необходимости подправь
    col_widths = [285, 285]

    # Создание таблицы
    signature_table = Table(signature_data, colWidths=col_widths)

    # Применяем объединения и стиль
    signature_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))

    y_sign = y2 - load_table._height + 20  # Или где тебе нужно
    x_sign = (width - sum(col_widths)) / 2

    signature_table.wrapOn(p, width, height)
    signature_table.drawOn(p, x_sign, y_sign)

    # Табличные данные
    time_data = [
        ["PICKUP", "DELIVERY", signarure2],
        ["Shipper Initials", "Receiver Initials", ''],
        [pickup_table, delivery_table, '']
    ]

    col1_widths = [142.5,142.5,285]

    time_table = Table(time_data, colWidths=col1_widths)

    time_table.setStyle(TableStyle([
        ('SPAN', (2, 0), (2, 2)),
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),



    ]))

    y_sign = y2 - signature_table._height - 150  # Или где тебе нужно
    x_sign = (width - sum(col1_widths)) / 2

    time_table.wrapOn(p, width, height)
    time_table.drawOn(p, x_sign, y_sign)

    # ✅ Завершаем PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    return HttpResponse(buffer, content_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename='BOL_{data.get('bolNumber', '00000')}.pdf'"
    })


BOL_COUNTER_FILE = os.path.join(settings.BASE_DIR, 'bol_counter.json')


@csrf_exempt
def get_bol_counters(request):
    print("📍 BOL_COUNTER_FILE path:", BOL_COUNTER_FILE)

    if request.method == 'GET':
        if not os.path.exists(BOL_COUNTER_FILE):
            with open(BOL_COUNTER_FILE, 'w') as f:
                json.dump({"bol": 1000, "load": 2000}, f)


        with open(BOL_COUNTER_FILE, 'r') as f:
            data = json.load(f)
        return JsonResponse(data)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def increment_bol_counters(request):
    if request.method == 'POST':
        # ✅ Если файл не существует, создаём его с начальными значениями
        if not os.path.exists(BOL_COUNTER_FILE):
            with open(BOL_COUNTER_FILE, 'w') as f:
                json.dump({"bol": 1000, "load": 2000}, f)

        # ✅ Читаем и обновляем
        with open(BOL_COUNTER_FILE, 'r+') as f:
            data = json.load(f)
            data["bol"] += 1
            data["load"] += 1
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        return JsonResponse({"status": "updated", "bol": data["bol"], "load": data["load"]})
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)




# Показать задачи, привязанные к контакту
def contact_tasks(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)
    tasks = contact.tasks.all()
    return render(request, 'crm/task_list.html', {'contact': contact, 'tasks': tasks})

# Добавить задачу
def add_task(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.contact = contact  # или task.company = contact.company если менял логику
            task.save()
            return redirect('contact_tasks', contact_id=contact.id)
    else:
        form = TaskForm()

    return render(request, 'crm/add_truck.html', {'form': form, 'contact': contact})



from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_stage(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            pipeline_id = data.get('id')
            new_stage = data.get('stage')
            new_order = data.get('order', 0)

            pipeline = PipeLine.objects.get(id=pipeline_id)
            pipeline.stage = new_stage
            pipeline.order = new_order
            pipeline.save()

            return JsonResponse({"status": "success", "stage": new_stage, "order": new_order})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)


from django.template.defaulttags import register
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])

def kanban_board(request):
    stages = ["new", "send_email", "meeting", "account", "deal"]
    pipeline = PipeLine.objects.select_related("contact", "contact__company").all()

    grouped = {stage: [] for stage in stages}
    for item in pipeline:
        grouped[item.stage].append(item)

    return render(request, "crm/kanban_board.html", {
        "stages": stages,
        "grouped_pipeline": grouped
    })


@csrf_exempt
def get_clients_grouped(request):
    if request.method == "GET":
        suppliers = Client.objects.filter(client_type='suppliers').values("id", "name")
        buyers = Client.objects.filter(client_type='buyers').values("id", "name")
        return JsonResponse({
            "suppliers": list(suppliers),
            "buyers": list(buyers)
        })

def get_companies_by_type(request):
    suppliers = Company.objects.filter(contacts__company_type="suppliers").distinct()
    buyers = Company.objects.filter(contacts__company_type="buyers").distinct()
    hauler = Company.objects.filter(contacts__company_type="hauler").distinct()

    data = {
        "suppliers": [{"id": c.id, "name": c.name} for c in suppliers],
        "buyers": [{"id": c.id, "name": c.name} for c in buyers],
        "hauler": [{"id": c.id, "name": c.name} for c in hauler],
    }
    return JsonResponse(data)


@csrf_exempt
def mark_shipment_done(request, shipment_id):
    if request.method == "POST":
        try:
            shipment = ScheduledShipment.objects.get(id=shipment_id)
            shipment.is_done = True
            shipment.save()
            return JsonResponse({"status": "done"})
        except ScheduledShipment.DoesNotExist:
            return JsonResponse({"status": "not found"}, status=404)
    return JsonResponse({"status": "invalid method"}, status=405)



def supply_list(request):
    # Получаем текущий месяц и год
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Получаем параметры фильтра из запроса
    selected_company_id = request.GET.get('company', '')
    month = request.GET.get('month', '') or str(current_month).zfill(2)
    year = request.GET.get('year', '') or str(current_year)


    # Фильтрация сделок
    deals = Deals.objects.all()

    if selected_company_id:
        deals = deals.filter(Q(buyer__id=int(selected_company_id)))

    if month and year:
        deals = deals.filter(date__month=int(month), date__year=int(year))
    elif month:  # Если указан только месяц
        deals = deals.filter(date__month=int(month))
    elif year:  # Если указан только год
        deals = deals.filter(date__year=int(year))

    # Итоги
    total_amount_buyer = deals.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_buyer_paid = deals.aggregate(Sum('total_income_loss'))[
                           'total_income_loss__sum'] or 0  # Итог для покупателя (например, прибыль или убыток)

    # Список компаний для выбора в фильтре
    companies = Company.objects.filter(contacts__company_type='buyers').distinct()



    # Получаем доступные года из базы данных для фильтрации
    years = Deals.objects.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct()

    # Список месяцев для фильтрации
    months = range(1, 13)  # Месяцы с 1 по 12

    # Контекст для шаблона
    context = {
        'deals': deals,
        'total_amount_buyer': total_amount_buyer,
        'total_buyer_paid': total_buyer_paid,  # Передаем total_buyer_paid в шаблон
        'companies': companies,
        'selected_company_id': int(selected_company_id) if selected_company_id.isdigit() else None,
        'month': month,
        'year': year,
        'years': sorted(years),  # Сортируем список лет для удобства
        'months': months,  # Месяцы для выпадающего списка
    }
    return render(request, 'crm/supply_list.html', context)



def sanitize_filename(name):
    name = name.strip()
    name = name.replace(' ', '_')
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def export_supply_list_pdf(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    import os
    from django.conf import settings
    from django.utils.text import slugify

    selected_company_id = request.GET.get('company', '')
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    now = datetime.now()

    deals = Deals.objects.all()
    if selected_company_id:
        deals = deals.filter(buyer__id=int(selected_company_id))
    if month:
        deals = deals.filter(date__month=int(month))
    if year:
        deals = deals.filter(date__year=int(year))

    first_deal = deals.first()
    total_field = "total_amount"

    data = [["Date", "Grade", "Net (MT)", "Price ($/MT)", "Amount ($)"]]
    for deal in deals:
        data.append([
            deal.date.strftime("%Y-%m-%d"),
            deal.grade,
            f"{deal.shipped_quantity:.4f}",
            f"${deal.buyer_price:.2f}",
            f"${deal.total_amount:.2f}",
        ])

    total_net = sum(deal.shipped_quantity for deal in deals)
    total_amount = sum(getattr(deal, total_field, 0) for deal in deals)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    current_y = height - 50

    logo_path = os.path.join(settings.BASE_DIR, 'crm', 'static', 'crm', 'images', 'cl2.png')
    if os.path.exists(logo_path):
        pdf.drawImage(ImageReader(logo_path), 30, current_y - 40, width=50, height=50, mask='auto')

    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.darkblue)
    pdf.drawRightString(width - 30, current_y - 10, "Local to Global Recycling Inc.")
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.black)
    pdf.drawRightString(width - 30, current_y - 23, "19090 Lougheed Hwy.")
    pdf.drawRightString(width - 30, current_y - 33, "Pitt Meadows, BC V3Y 2M6")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, current_y - 10, "Shipment Summary")

    # 📍 Customer info
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, height - 160, "Customer:")

    customer_details = []
    if first_deal and first_deal.buyer:
        customer_details.append(first_deal.buyer.name)
        contact = first_deal.buyer.contacts.filter(address__isnull=False).first()
        if contact and contact.address:
            customer_details.extend(contact.address.strip().split('\n'))
        else:
            customer_details.append("Address not available")
    else:
        customer_details = ["Unknown"]

    pdf.setFont("Helvetica", 10)
    y_position = height - 175
    for line in customer_details:
        pdf.drawString(85, y_position, line.strip())
        y_position -= 15

    # 📊 Таблица под адресом клиента + небольшой отступ
    table_top_y = y_position - 20
    table = Table(data, colWidths=[80, 140, 60, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    # Определим высоту таблицы для расчёта позиции итогов
    table_width, table_height = table.wrap(0, 0)
    table.drawOn(pdf, 30, table_top_y - table_height)

    # 📉 Итоги ниже таблицы
    summary_y = table_top_y - table_height - 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, summary_y, f"Total Net: {total_net:.2f} MT")
    pdf.drawString(30, summary_y - 20, f"Total Amount: ${total_amount:.2f}")

    # 📉 Итоги (ниже таблицы)
    summary_y = table_top_y - table_height - 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, summary_y, f"Total Net: {total_net:.2f} MT")
    pdf.drawString(30, summary_y - 20, f"Total Amount: ${total_amount:.2f}")

    # 📊 Расчёт итогов по каждому грейду
    pdf.setFont("Helvetica", 10)
    grade_summary = {}

    for deal in deals:
        key = (deal.grade, deal.buyer_price)
        if key not in grade_summary:
            grade_summary[key] = {"amount": 0, "net": 0}
        grade_summary[key]["net"] += deal.shipped_quantity
        grade_summary[key]["amount"] += deal.total_amount


    y = summary_y - 50  # ⬇ Начинаем ниже итогов

    for (grade, price), values in grade_summary.items():
        amount = values["amount"]
        net = values["net"]
        pdf.drawString(30, y, f"{grade} (${price:.2f}) – {net:.2f} MT – ${amount:.2f} ")
        y -= 15  # отступ между строками

    # 📁 Название файла
    raw_name = first_deal.buyer.name if first_deal and first_deal.buyer else "Unknown"
    safe_name = slugify(raw_name)
    month_str = datetime.strptime(month, "%m").strftime("%b") if month else now.strftime("%b")
    year_str = year if year else now.strftime("%Y")
    filename = f"L2G_{safe_name}_Supply_List_{month_str}_{year_str}.pdf"

    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


from datetime import timedelta, date
from crm.models import ScheduledShipment


def generate_recurring_shipments():
    print("🚀 Функция генерации повторов ЗАПУЩЕНА")

    today = date.today()
    end_date = today + timedelta(weeks=52)  # 🔁 Генерируем на год вперёд

    # Получаем шаблоны
    recurring_shipments = ScheduledShipment.objects.filter(is_recurring=True, is_done=False)
    print(f"📦 Проверка повторяющихся отгрузок на {today} ({len(recurring_shipments)} шаблонов)")

    for shipment in recurring_shipments:
        current_date = shipment.date

        while True:
            # 🗓 Вычисляем следующую дату
            if shipment.recurrence_type == 'weekly':
                current_date += timedelta(weeks=1)
            elif shipment.recurrence_type == 'biweekly':
                current_date += timedelta(weeks=2)
            elif shipment.recurrence_type == 'monthly':
                try:
                    # Пробуем сдвинуть месяц
                    next_month = current_date.month + 1
                    year = current_date.year + (next_month - 1) // 12
                    month = (next_month - 1) % 12 + 1
                    current_date = current_date.replace(year=year, month=month)
                except ValueError:
                    print(f"⚠️ Пропущено: невозможно установить дату для {shipment}")
                    break

            if current_date > end_date:
                break

            # Проверяем, не существует ли уже такая отгрузка
            exists = ScheduledShipment.objects.filter(
                supplier=shipment.supplier,
                buyer=shipment.buyer,
                date=current_date,
                time=shipment.time,
                grade=shipment.grade
            ).exists()

            if exists:
                print(f"⏩ Уже есть: {current_date} — пропущено.")
                continue

            # Создаём новую отгрузку
            ScheduledShipment.objects.create(
                supplier=shipment.supplier,
                buyer=shipment.buyer,
                date=current_date,
                time=shipment.time,
                grade=shipment.grade,
                is_recurring=False  # 📌 Повтор создан — это не шаблон
            )

            print(f"✅ Создана отгрузка на {current_date} для {shipment.supplier} → {shipment.buyer} ({shipment.grade})")


def ai_dashboard(request):
    # Выбираем убыточные сделки
    problem_deals = Deals.objects.filter(total_income_loss__lt=0)
    deal_issues_count = problem_deals.count()

    return render(request, 'crm/ai_dashboard/ai_dashboard.html', {
        'deal_issues_count': deal_issues_count
    })

# views.py
from crm.ai_dashboard.deal_recommendations import analyze_deals

def deal_recommendations(request):
    recommendations = analyze_deals()
    return render(request, 'crm/ai_dashboard/deal_recommendations.html', {
        'recommendations': recommendations
    })

from crm.ai_dashboard.shipment_predictor import predict_shipments

def shipment_predictions(request):
    predictions = predict_shipments()
    return render(request, 'crm/ai_dashboard/shipment_predictor.html', {
        'predictions': predictions
    })

from crm.ai_dashboard.client_monitor import find_inactive_clients,INACTIVITY_DAYS_THRESHOLD

def client_monitor_view(request):
    inactive_clients = find_inactive_clients()
    return render(request, 'crm/ai_dashboard/client_monitor.html', {
        'inactive_clients': inactive_clients,
        'threshold': INACTIVITY_DAYS_THRESHOLD
    })

from crm.ai_dashboard.email_generator import generate_reminder_email

def generate_email_view(request, company_id):
    from crm.models import Company
    from crm.ai_dashboard.email_generator import generate_reminder_email

    company = Company.objects.get(id=company_id)
    email_text = generate_reminder_email(company.name)

    return render(request, 'crm/ai_dashboard/generated_email.html', {
        'company': company,
        'email_text': email_text
    })

from crm.ai_dashboard.insight_engine import get_pie_chart_data
from django.http import JsonResponse

def ai_pie_stats(request):
    data = get_pie_chart_data()
    return JsonResponse(data)

from crm.models import Deals
from django.db.models import Sum

def get_problem_suppliers():
    suppliers = (
        Deals.objects
        .filter(total_income_loss__lt=0, supplier__isnull=False)
        .values('supplier__name')
        .annotate(total_loss=Sum('total_income_loss'))
        .order_by('total_loss')
    )

    max_loss = abs(min(s['total_loss'] for s in suppliers)) or 1  # защита от деления на 0

    result = []
    for s in suppliers:
        loss = abs(s['total_loss'])
        percent = int((loss / max_loss) * 100)
        result.append({
            'name': s['supplier__name'],
            'loss': round(loss, 2),
            'percent': percent
        })

    return result


from django.utils.timezone import now

def get_supplier_monthly_stats(request):
    current_year = now().year

    # Берём сделки по году, сгруппированные по supplier и месяцу
    data = (
        Deals.objects.filter(
            date__year=current_year,
            supplier__isnull=False
        )
        .values('supplier__name', 'date__month')
        .annotate(total=Sum('total_income_loss'))
        .order_by('supplier__name', 'date__month')
    )

    # Строим структуру: {supplier_name: [month1, ..., month12]}
    result = {}
    for entry in data:
        name = entry['supplier__name']
        month = entry['date__month']
        total = round(entry['total'], 2)

        if name not in result:
            result[name] = [0] * 12

        result[name][month - 1] = total

    return JsonResponse(result)

def get_buyer_supplier_map(request):
    from crm.models import Deals
    result = {}
    qs = Deals.objects.filter(buyer__isnull=False, supplier__isnull=False).values("buyer__name", "supplier__name").distinct()

    for row in qs:
        buyer = row["buyer__name"]
        supplier = row["supplier__name"]
        result.setdefault(buyer, []).append(supplier)

    return JsonResponse(result)



from crm.ai_dashboard.insight_engine import (
    get_top_clients,
    get_worst_deals,
    get_top_suppliers,
    get_problem_suppliers,
    get_clients_with_drop,
    get_supplier_monthly_profit_and_tonnage,
    get_pie_chart_data
)
from django.views.decorators.http import require_GET
from collections import defaultdict

def insight_dashboard(request):
    # # основные блоки для шаблона
    top_clients = get_top_clients()                         # топ клиентов по прибыли
    worst_deals = get_worst_deals()                         # худшие сделки этого месяца
    top_suppliers = get_top_suppliers()                     # топ поставщиков по прибыли
    problem_suppliers = get_problem_suppliers()             # проблемные поставщики (месяц)
    dropped_clients = get_clients_with_drop()               # клиенты с падением оборота

    # # рендерим HTML, остальное фронт подтянет через fetch()
    return render(request, 'crm/ai_dashboard/insights.html', {
        'top_clients': top_clients,
        'worst_deals': worst_deals,
        'top_suppliers': top_suppliers,
        'problem_suppliers': problem_suppliers,
        'dropped_clients': dropped_clients,
    })


@require_GET
def supplier_monthly_api(request):
    # # отдаём объединённую структуру: { "Supplier A": {"profit":[..12..], "tonnage":[..12..]}, ... }
    data = get_supplier_monthly_profit_and_tonnage()        # считаем в engine
    return JsonResponse(data, safe=True)                    # safe=True т.к. dict


@require_GET
def buyer_suppliers_api(request):
    # # строим мэппинг: покупатель -> список его поставщиков (по факту сделок)
    mapping = defaultdict(set)                              # set чтобы убрать дубликаты

    qs = (Deals.objects
          .filter(buyer__isnull=False, supplier__isnull=False)   # обе стороны заданы
          .values('buyer__name', 'supplier__name')               # берём имена
          )

    for row in qs:
        buyer = row['buyer__name'] or 'Unknown'             # подстраховка от NULL
        supplier = row['supplier__name'] or 'Unknown'       # подстраховка от NULL
        mapping[buyer].add(supplier)                        # добавляем связь

    # # превращаем set -> list для JSON
    data = {buyer: sorted(list(suppliers)) for buyer, suppliers in mapping.items()}
    return JsonResponse(data, safe=True)


@require_GET
def pie_stats_api(request):
    # # отдаём данные для пирогов: {"suppliers": {...}, "buyers": {...}}
    stats = get_pie_chart_data()                            # считает engine
    return JsonResponse(stats, safe=True)



from django.views.decorators.http import require_http_methods
import math
@require_http_methods(["GET", "POST"])
def add_truck(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id)
    company = contact.company

    if contact.company_type != "hauler":
        return HttpResponse("❌ Only hauler contacts can have trucks", status=400)

    if request.method == "POST":
        max_tons = float(request.POST.get("max_tons", 0))      # максимум тонн
        base_cost = float(request.POST.get("base_cost", 0))    # базовая цена
        max_spots = int(request.POST.get('max_spots', 0))

        # 🔁 Изменить расчёт max_bales:
        if max_tons > 0 and max_spots > 0:
            max_bales = max_spots  # 💡 теперь не рассчитываем, а вводим напрямую
        else:
            max_bales = 0

        # ✅ Сохраняем
        TruckProfile.objects.create(
            company=company,
            max_bales=max_bales,
            max_tons=max_tons,
            max_spots=max_spots,
            base_cost=base_cost
        )

        return redirect("view_contact", id=contact_id)

    return render(request, "crm/add_truck.html", {"contact": contact})


def delete_truck(request, id):
    truck = get_object_or_404(TruckProfile, id=id)

    # 🧩 Получаем первый контакт этой компании (предполагаем, что он есть)
    contact = Contact.objects.filter(company=truck.company).first()
    if not contact:
        return redirect('contacts_list')  # fallback, если что-то пошло не так

    truck.delete()
    return redirect('view_contact', id=contact.id)