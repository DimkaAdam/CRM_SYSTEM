from django.db import models
from django.utils import timezone
from django.db.models import F
from django.conf import settings

class Client(models.Model):
    contact_type = [
        ('suppliers', 'Suppliers'),
        ('hauler','Hauler'),
        ("buyers","Buyers")
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True,null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    client_type = models.CharField(max_length=10,choices=contact_type, default='suppliers')

    def __str__(self):
        return self.company

class Company(models.Model):
    name = models.CharField(max_length=200, unique=True)
    unique_number = models.CharField(max_length=255, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Проверяем, создается ли объект впервые
            super().save(*args, **kwargs)  # Сохраняем объект, чтобы получить pk
            self.unique_number = f"COMP{self.pk:04d}"
            # Обновляем только поле unique_number
            Company.objects.filter(pk=self.pk).update(unique_number=self.unique_number)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Contact(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="contacts")
    address = models.CharField(max_length=255, blank=True, null=True)
    company_type = models.CharField(
        max_length=10,
        choices=[
            ('suppliers', 'Suppliers'),
            ('hauler', 'Hauler'),
            ('buyers', 'Buyers'),
        ],
        default='suppliers'
    )
    def __str__(self):
        return f'{self.company.name} ({self.company_type})'

class Employee(models.Model):
    contact = models.ForeignKey(Contact, related_name='employees', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    position = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

class Deals(models.Model):
    date = models.DateTimeField(default=timezone.now)  # Дата сделки
    supplier = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='deals_as_supplier')
    buyer = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='deals_as_buyer', null=True, blank=True)
    grade = models.CharField(max_length=255, choices=[(key, key) for key in settings.MATERIALS_LIST.keys()])
    shipped_quantity = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, default=0)  # Отправленный объем (тонны, паллеты и т.д.)
    shipped_pallets = models.PositiveIntegerField(default=0)  # Количество паллет (по умолчанию 0)
    scale_ticket = models.CharField(max_length=50, blank=True, null=True)  # Номер талона на весы (может быть пустым)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, default=0)  # Принятый объем (по умолчанию 0)
    received_pallets = models.IntegerField(default=0)  # Количество паллет, принятых (по умолчанию 0)
    supplier_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Цена поставщика (может быть пустым)
    supplier_currency = models.CharField(max_length=10, default="CAD")  # Валюта поставщика (по умолчанию "CAD")
    supplier_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Сумма поставщика (может быть пустым)
    buyer_price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена покупателя
    buyer_currency = models.CharField(max_length=10, default="CAD")  # Валюта покупателя (по умолчанию "CAD")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)  # Итоговая сумма сделки
    invoice_number = models.CharField(max_length=50, blank=True, null=True)  # Номер счета (может быть пустым)
    paid_date = models.DateField(blank=True, null=True)  # Дата оплаты (может быть пустым)
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2,default=0)  # Стоимость транспорта
    transport_company = models.CharField(max_length=255, blank=True, null=True)  # Название транспортной компании (может быть пустым)
    total_income_loss = models.DecimalField(max_digits=10, decimal_places=2,default=0)  # Общий доход/убыток



    def save(self, *args, **kwargs):
        # Убедимся, что все значения корректны для расчетов
        self.received_quantity = self.received_quantity or 0
        self.buyer_price = self.buyer_price or 0
        self.transport_cost = self.transport_cost or 0
        self.supplier_total = self.supplier_total or 0

        # Рассчитываем итоговую сумму сделки
        self.total_amount = self.received_quantity * self.buyer_price

        # Если есть supplier_price, рассчитываем supplier_total
        if self.supplier_price is not None and self.received_quantity is not None:
            self.supplier_total = self.received_quantity * self.supplier_price

        # Рассчитываем общий доход/убыток
        self.total_income_loss = self.total_amount - (self.transport_cost + self.supplier_total)

        super().save(*args, **kwargs)

        # Преобразуем self.shipped_pallets в число
        shipped_pallets_count = float(self.shipped_pallets) if self.shipped_pallets else 0

        # Обновляем или создаем запись о паллетах для компании-поставщика
        if self.supplier:
            supplier_pallets, created = CompanyPallets.objects.get_or_create(
                company_name=self.supplier,
                defaults={'pallets_count': 0}  # Если записи нет, создаем с нулевым значением
            )
            supplier_pallets.pallets_count -= shipped_pallets_count
            supplier_pallets.save()

        # Обновляем или создаем запись о паллетах для компании-покупателя
        if self.buyer:
            buyer_pallets, created = CompanyPallets.objects.get_or_create(
                company_name=self.buyer,
                defaults={'pallets_count': 0}  # Если записи нет, создаем с нулевым значением
            )
            buyer_pallets.pallets_count += int(self.received_pallets)
            buyer_pallets.save()

    def __str__(self):
        return f"Deal: {self.date} - {self.supplier} to {self.buyer}"


class Task(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class CompanyPallets(models.Model):
    company_name = models.ForeignKey(Company,on_delete=models.CASCADE, related_name='pallets')
    pallets_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.company_name}: {self.pallets_count} pallets"


# materials names
class Material(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ContactMaterial(models.Model):
    contact = models.ForeignKey('Contact', on_delete=models.CASCADE, related_name='contact_materials')
    material = models.CharField(max_length=255, choices=[(key, key) for key in settings.MATERIALS_LIST.keys()])
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.contact.company.name} - {self.material} (${self.price or 'Not set'})"



class PipeLine(models.Model):
    STAGES = [
        ('new', 'New'),
        ('send_email', 'Send Email'),
        ('meeting', 'Meeting'),
        ('account', 'Account'),
        ('deal', 'Deal'),
    ]

    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, blank=True)  # Связь с моделью компании
    stage = models.CharField(max_length=20, choices=STAGES, default='new')  # Этап воронки

    def __str__(self):
        return f"{self.company.name} - {self.get_stage_display()}"




class Event(models.Model):
    title = models.CharField(max_length=200)  # Название события
    start = models.DateTimeField()  # Дата и время начала
    end = models.DateTimeField(null=True, blank=True)  # Дата и время окончания (необязательно)
    all_day = models.BooleanField(default=False)  # Весь день

    def __str__(self):
        return self.title
