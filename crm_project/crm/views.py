from django.core.serializers import serialize
from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Deals, Task, PipeLine, CompanyPallets, Company, Contact, Employee
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .serializers import ClientSerializer
from .serializers import DealSerializer
from .forms import ContactForm
import openpyxl
from django.http import HttpResponse

from django.db.models import Sum


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

def company_detail(request, company_id):
    # Получаем объект компании по id
    company = get_object_or_404(Company, id=company_id)

    # Получаем все контакты этой компании
    contacts = company.contacts.all()

    return render(request, 'crm/company_detail.html', {
        'company': company,
        'contacts': contacts,
    })


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
        serializer = DealSerializer(data=request.data)
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
    total_sale = Deals.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_pallets = Deals.objects.aggregate(Sum('shipped_pallets'))['shipped_pallets__sum'] or 0
    transportation_fee = Deals.objects.aggregate(Sum('transport_cost'))['transport_cost__sum'] or 0
    suppliers_total = Deals.objects.aggregate(Sum('supplier_total'))['supplier_total__sum'] or 0
    mt_occ11 = Deals.objects.filter(grade="OCC11").aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    mt_plastic = Deals.objects.filter(grade="Plastic").aggregate(Sum('received_quantity'))[
                     'received_quantity__sum'] or 0
    mt_mixed_containers = Deals.objects.filter(grade="Mixed-containers").aggregate(Sum('received_quantity'))['received_quantity__sum'] or 0
    income = Deals.objects.filter(total_income_loss__gt=0).aggregate(Sum('total_income_loss'))['total_income_loss__sum'] or 0

    # Данные о палетах
    company_pallets = CompanyPallets.objects.select_related('company_name')

    # Сброс палет (если пользователь отправил форму)
    if request.method == 'POST' and 'reset_pallets' in request.POST:
        CompanyPallets.objects.update(pallets_count=0)

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
    }
    return render(request, 'crm/sales_analytics.html', context)