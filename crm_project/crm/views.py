from django.core.serializers import serialize
from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Deals, Task, PipeLine, CompanyPallets, Company, Contact, Employee, ContactMaterial
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import ClientSerializer
from .serializers import DealSerializer
from .forms import ContactForm, CompanyForm, ContactMaterialForm, DealForm
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import datetime
from django.db.models.functions import ExtractYear
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from openpyxl.styles import Font, PatternFill, Alignment




def index(request):
    return render(request, 'crm/index.html')


def client_list(request):
    clients = Client.objects.all()

    supplier = clients.filter(client_type='suppliers')
    buyer = clients.filter(client_type='buyers')

    return render(request, 'crm/client_list.html', {
        'clients': clients,
        'suppliers': supplier,
        'buyers': buyer,
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

    if request.method == "POST":
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            return redirect('view_contact', id = contact.id)
    else:
        form=ContactForm(instance=contact)


    return render(request, 'crm/view_contact.html', {'contact': contact, 'form': form})


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

    return render(request, 'add_employee.html', {'contact': contact})

def delete_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        employee.delete()
        return redirect('contacts')


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
    today = datetime.today()
    current_month = today.month
    current_year = today.year

    # Получаем базовый набор данных
    deals = Deals.objects.all()

    # Фильтруем компании по типу через связанные контакты
    suppliers = Company.objects.filter(contacts__company_type="suppliers").distinct()  # Только поставщики
    buyers = Company.objects.filter(contacts__company_type="buyers").distinct()  # Только покупатели

    # Получаем параметры фильтра из запроса
    month = request.GET.get('month', str(current_month).zfill(2))  # Текущий месяц по умолчанию
    year = request.GET.get('year', str(current_year))  # Текущий год по умолчанию

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
    }

    # Рендерим страницу с переданным контекстом
    return render(request, 'crm/deal_list.html', context)

from datetime import datetime

def export_deals_to_excel(request):
    from openpyxl.utils import get_column_letter

    # Получаем текущий месяц и год
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Создаем книгу Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Deals"

    # Настройка стилей для заголовков
    header_font = Font(name="Arial", bold=True, color="FFFFFF")  # Белый жирный текст
    header_fill = PatternFill(start_color="87CEEB", end_color="87CEEB", fill_type="solid")  # Светло-синий фон
    header_alignment = Alignment(horizontal="center", vertical="center")  # Центрирование текста

    # Заголовки столбцов
    headers = [
        'Date', 'Supplier', 'Buyer', 'Grade', 'Shipped Qty', 'Pallets',
        'Received Qty', 'Pallets', 'Supplier Price', 'Supplier Paid Amount', 'Buyer Price',
        'Total Amount', 'Transport Cost', 'Houler', 'Income/Loss'
    ]
    ws.append(headers)

    # Применяем стили к заголовкам
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)  # Получаем ячейку
        cell.font = header_font  # Применяем стиль шрифта
        cell.fill = header_fill  # Применяем цвет фона
        cell.alignment = header_alignment  # Применяем выравнивание

    # Получаем сделки только за текущий месяц
    deals = Deals.objects.select_related('supplier', 'buyer').filter(
        date__year=current_year,
        date__month=current_month
    )

    for row_num, deal in enumerate(deals, start=2):
        formatted_date = deal.date.strftime('%Y-%m') if deal.date else ''
        ws.append([
            formatted_date,
            deal.supplier.name if deal.supplier else '',
            deal.buyer.name if deal.buyer else '',
            deal.grade,
            deal.shipped_quantity,
            deal.shipped_pallets,
            deal.received_quantity,
            deal.received_pallets,
            deal.supplier_price,
            deal.supplier_total,
            deal.buyer_price,
            deal.total_amount,
            deal.transport_cost,
            deal.transport_company,
            deal.total_income_loss
        ])

    # Начало сводной секции справа от основной таблицы
    summary_col_start = len(headers) + 2  # Первая колонка справа от таблицы
    summary_data = [
        ("TOTAL SALE", "=SUM(L2:L30)".format(len(deals) + 1)),  # Общая продажа (Total Amount)
        ("# of pallets", "=SUM(F2:F30)".format(len(deals) + 1)),  # Общее количество паллет
        ("Transportation cost", "=SUM(M2:M30)".format(len(deals) + 1)),  # Транспортные расходы
        ("Suppliers", "=SUM(J2:J30)".format(len(deals) + 1)),  # Итоги для поставщиков
        ("MT OCC11",
         "=SUMPRODUCT((D2:D30=\"OCC11\")+(D2:D30=\"OCC 11\")+(D2:D30=\"OCC 11 Bale String\")+(D2:D30=\"Loose OCC\"), E2:E30)".format(
             len(deals) + 1, len(deals) + 1, len(deals) + 1, len(deals) + 1, len(deals) + 1, len(deals) + 1
         )),  # MT OCC11
        ("MT Plastic", "=SUMIF(D2:D30, \"Flexible Plastic\", E2:E30)".format(len(deals) + 1, len(deals) + 1)),  # MT Plastic
        ("MT Mixed-containers", "=SUMIF(D2:D30, \"Mixed Container\", E2:E30)".format(len(deals) + 1, len(deals) + 1)),  # MT Mixed-containers
        ("INCOME", "=SUM(O2:O30)".format(len(deals) + 1))  # Общая прибыль/убыток
    ]

    # Заполняем сводные данные
    for row_num, (label, value) in enumerate(summary_data, start=2):
        label_cell = ws.cell(row=row_num, column=summary_col_start)  # Ячейка для заголовка
        label_cell.value = label
        label_cell.font = Font(bold=True)  # Жирный текст
        label_cell.alignment = Alignment(horizontal="right")  # Выравнивание по правому краю

        value_cell = ws.cell(row=row_num, column=summary_col_start + 1)  # Ячейка для значения
        value_cell.value = value  # Значение или формула
        if value.startswith("="):  # Если это формула
            value_cell.number_format = '#,##0.00'  # Формат чисел с запятыми
        else:
            value_cell.font = Font(color="007BFF", italic=True)  # Стилизация текста

    # Автоматическая подгонка ширины столбцов
    for col in ws.columns:
        max_length = 0
        column = get_column_letter(col[0].column)  # Получаем букву столбца
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
    response['Content-Disposition'] = f'attachment; filename=deals_{current_year}_{current_month}.xlsx'
    wb.save(response)
    return response




def get_deal_details(request, deal_id):
    deal = get_object_or_404(Deals, id=deal_id)
    return JsonResponse({
        'id': deal.id,
        'date': deal.date.strftime('%Y-%m-%d'),
        'supplier': deal.supplier.name,
        'buyer': deal.buyer.name,
        'grade': deal.grade,
        'shipped_quantity': deal.shipped_quantity,
        'received_quantity': deal.received_quantity,
        'supplier_price': deal.supplier_price,
        'buyer_price': deal.buyer_price,
        'total_amount': deal.total_amount,
        'transport_cost': deal.transport_cost,
        'transport_company': deal.transport_company,
    })


@csrf_exempt
def edit_deal(request, deal_id):
    deal = get_object_or_404(Deals, id=deal_id)

    if request.method == 'POST':
        data = json.loads(request.body)

        # Получаем объект Company для supplier и buyer по их ID
        supplier_id = data.get('supplier')
        buyer_id = data.get('buyer')

        # Убедитесь, что ID являются валидными
        if supplier_id:
            deal.supplier = get_object_or_404(Company, id=supplier_id)
        if buyer_id:
            deal.buyer = get_object_or_404(Company, id=buyer_id)

        # Преобразуем данные в числовые значения
        deal.received_quantity = Decimal(data.get('received_quantity', deal.received_quantity))
        deal.buyer_price = Decimal(data.get('buyer_price', deal.buyer_price))
        deal.supplier_price = Decimal(data.get('supplier_price', deal.supplier_price))

        # Обновляем остальные поля
        deal.date = data.get('date', deal.date)
        deal.grade = data.get('grade', deal.grade)
        deal.shipped_quantity = data.get('shipped_quantity', deal.shipped_quantity)
        deal.shipped_pallets = data.get('shipped_pallets', deal.shipped_pallets)
        deal.received_pallets = data.get('received_pallets', deal.received_pallets)
        deal.transport_cost = Decimal(data.get('transport_cost', deal.transport_cost))
        deal.transport_company = data.get('transport_company', deal.transport_company)

        # Выполняем расчеты для итоговых сумм
        deal.total_amount = deal.received_quantity * deal.buyer_price
        deal.supplier_total = deal.received_quantity * deal.supplier_price
        deal.total_income_loss = deal.total_amount - (deal.supplier_total + deal.transport_cost)

        # Сохраняем обновленную сделку
        deal.save()

        # Возвращаем успешный ответ с данными обновленной сделки
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
# TACKS
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
        serializer = DealSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deals.objects.all()
    serializer_class = DealSerializer





def sales_analytics(request):
    # Получаем текущий месяц и год
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Получаем параметры фильтра из запроса
    month = request.GET.get('month', str(current_month).zfill(2))  # Текущий месяц по умолчанию
    year = request.GET.get('year', str(current_year))  # Текущий год по умолчанию

    # Данные о сделках с учетом фильтра по месяцу и году
    deals_filter = Deals.objects.all()
    if month and year:
        deals_filter = deals_filter.filter(date__month=int(month), date__year=int(year))
    elif month:  # Если указан только месяц
        deals_filter = deals_filter.filter(date__month=int(month))
    elif year:  # Если указан только год
        deals_filter = deals_filter.filter(date__year=int(year))

    suppliers_income = deals_filter.values('supplier').annotate(total_income_loss=Sum('total_income_loss'))
    suppliers_income_dict = {
        contact.company.name: float(entry['total_income_loss'] or 0)
        for entry in suppliers_income
        for contact in Contact.objects.filter(company__id=entry['supplier'])
    }

    total_deals = deals_filter.count()
    total_sale = deals_filter.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_pallets = deals_filter.aggregate(Sum('shipped_pallets'))['shipped_pallets__sum'] or 0
    transportation_fee = deals_filter.aggregate(Sum('transport_cost'))['transport_cost__sum'] or 0
    suppliers_total = deals_filter.aggregate(Sum('supplier_total'))['supplier_total__sum'] or 0
    mt_occ11 = deals_filter.filter(grade="OCC11").aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    mt_plastic = deals_filter.filter(grade="Flexible Plastic").aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    mt_mixed_containers = deals_filter.filter(grade="Mixed Container").aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    income = deals_filter.aggregate(Sum('total_income_loss'))['total_income_loss__sum'] or 0

    # Данные о палетах
    company_pallets = CompanyPallets.objects.select_related('company_name')

    # Сброс палет (если пользователь отправил форму)
    if request.method == 'POST' and 'reset_pallets' in request.POST:
        CompanyPallets.objects.update(pallets_count=0)

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
    return render(request, 'crm/sales_analytics.html', context)


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