# ai_dashboard/insight_engine.py

from crm.models import Deals, Company
from django.db.models import Sum
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
from decimal import Decimal

def get_top_clients(limit=5):
    # Возвращает топ клиентов по прибыли
    top = (
        Deals.objects
        .values('buyer__name')
        .annotate(total_profit=Sum('total_income_loss'))
        .order_by('-total_profit')[:limit]
    )
    return top

def get_top_suppliers():
    return Deals.objects.filter(
        supplier__isnull=False
    ).values('supplier__name').annotate(
        total_profit=Sum('total_income_loss')
    ).order_by('-total_profit')[:5]

def get_problem_suppliers():
    current_date = now()

    # Получаем всех поставщиков с убытками за текущий месяц
    suppliers = (
        Deals.objects
        .filter(
            supplier__isnull=False,
            date__month=current_date.month,
            date__year=current_date.year
        )
        .values('supplier__name')
        .annotate(total_loss=Sum('total_income_loss'))
        .filter(total_loss__lt=0)
        .order_by('total_loss')
    )

    # Определим максимальный убыток для нормализации процентов
    max_loss = abs(min(s['total_loss'] for s in suppliers)) if suppliers else 1

    # Сформируем список словарей для шаблона
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

def get_worst_deals(limit=5):
    today = now()
    worst = (
        Deals.objects
        .filter(
            total_income_loss__lt=0,
            date__year=today.year,
            date__month=today.month
        )
        .order_by('total_income_loss')[:limit]
    )
    return worst

def get_clients_with_drop(threshold_ratio=0.5):
    today = now()

    current_year = today.year
    current_month = today.month

    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    prev_data = (
        Deals.objects.filter(date__year=prev_year, date__month=prev_month)
        .values('buyer')
        .annotate(total_prev=Sum('total_amount'))
    )

    curr_data = (
        Deals.objects.filter(date__year=current_year, date__month=current_month)
        .values('buyer')
        .annotate(total_curr=Sum('total_amount'))
    )

    prev_map = {item['buyer']: item['total_prev'] for item in prev_data}
    curr_map = {item['buyer']: item['total_curr'] for item in curr_data}

    dropped_clients = []

    threshold_decimal = Decimal(str(threshold_ratio))  # 🛠 преобразуем

    for buyer_id, prev_total in prev_map.items():
        curr_total = curr_map.get(buyer_id, Decimal("0"))

        if prev_total and curr_total < prev_total * threshold_decimal:
            try:
                buyer = Company.objects.get(id=buyer_id)
                dropped_clients.append({
                    "buyer": buyer,
                    "last_month": round(prev_total, 2),
                    "this_month": round(curr_total, 2),
                    "drop_percent": round(float(Decimal("100") * (1 - curr_total / prev_total)), 1)
                })
            except Company.DoesNotExist:
                continue

    return dropped_clients

def get_pie_chart_data():
    suppliers = (
        Deals.objects.filter(supplier__isnull=False)
        .values('supplier__name')
        .annotate(value=Sum('total_income_loss'))
    )
    buyers = (
        Deals.objects.filter(buyer__isnull=False)
        .values('buyer__name')
        .annotate(value=Sum('total_income_loss'))
    )

    supplier_data = {item['supplier__name']: float(item['value']) for item in suppliers}
    buyer_data = {item['buyer__name']: float(item['value']) for item in buyers}

    return {
        "suppliers": supplier_data,
        "buyers": buyer_data,
    }

def get_supplier_monthly_data():
    from collections import defaultdict

    current_year = now().year

    # Получаем сделки по году, сгруппированные по поставщику и месяцу
    data = (
        Deals.objects
        .filter(
            supplier__isnull=False,
            date__year=current_year
        )
        .values('supplier__name', 'date__month')
        .annotate(total=Sum('total_income_loss'))
        .order_by('supplier__name', 'date__month')
    )

    result = defaultdict(lambda: [0] * 12)

    for entry in data:
        name = entry['supplier__name']
        month = entry['date__month']
        total = round(entry['total'], 2) if entry['total'] is not None else 0
        result[name][month - 1] = total

    return dict(result)
