# ai_dashboard/insight_engine.py

from crm.models import Deals, Company
from django.utils import timezone
from django.utils.timezone import now
from decimal import Decimal
from collections import defaultdict
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta                      # удобные сдвиги дат
from django.db.models.functions import TruncMonth                     # группировка по месяцам
from django.http import JsonResponse

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
        .values('supplier')
        .annotate(total_prev=Sum('shipped_quantity'))
    )

    curr_data = (
        Deals.objects.filter(date__year=current_year, date__month=current_month)
        .values('supplier')
        .annotate(total_curr=Sum('shipped_quantity'))
    )

    prev_map = {item['supplier']: item['total_prev'] for item in prev_data}
    curr_map = {item['supplier']: item['total_curr'] for item in curr_data}

    dropped_clients = []

    threshold_decimal = Decimal(str(threshold_ratio))  # 🛠 преобразуем

    for supplier_id, prev_total in prev_map.items():
        curr_total = curr_map.get(supplier_id, Decimal("0"))

        if prev_total and curr_total < prev_total * threshold_decimal:
            try:
                supplier = Company.objects.get(id=supplier_id)
                dropped_clients.append({
                    "supplier": supplier,
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

def get_supplier_monthly_profit_and_tonnage():
    current_year = now().year

    data = (
        Deals.objects
        .filter(
            supplier__isnull=False,
            date__year=current_year
        )
        .values('supplier__name', 'date__month')
        .annotate(
            total_profit=Sum('total_income_loss'),
            total_tonnage=Sum('shipped_quantity'),
        )
        .order_by('supplier__name', 'date__month')
    )

    result = defaultdict(lambda: {'profit': [0.0] * 12, 'tonnage': [0.0] * 12})

    for entry in data:
        name = entry['supplier__name'] or 'Unknown'
        month_idx = (entry['date__month'] or 1) - 1

        profit = float(entry['total_profit'] or 0.0)
        tonnage = float(entry['total_tonnage'] or 0.0)

        result[name]['profit'][month_idx] = round(profit, 2)
        result[name]['tonnage'][month_idx] = round(tonnage, 2)

    return dict(result)


DATE_FIELD = "date"

def _month_bounds(d):
    first = d.replace(day=1)
    next_first = first.replace(year=first.year+1, month=1) if first.month == 12 else first.replace(month=first.month+1)
    return first, next_first

def _range_for_field(start_d, end_d, is_dt):
    if is_dt:
        from django.utils.timezone import make_aware
        return make_aware(datetime.combine(start_d, time.min)), make_aware(datetime.combine(end_d, time.min))
    return start_d, end_d

def compute_kpi():
    field = Deals._meta.get_field(DATE_FIELD)
    is_dt = field.get_internal_type() in ("DateTimeField",)

    today = timezone.localdate()
    s_d, e_d = _month_bounds(today)
    s, e = _range_for_field(s_d, e_d, is_dt)

    qs = Deals.objects.filter(**{f"{DATE_FIELD}__gte": s, f"{DATE_FIELD}__lt": e})

    # если за текущий месяц пусто — последние 30 дней
    if not qs.exists():
        last30 = timezone.localdate() - timedelta(days=30)
        s, e = _range_for_field(last30, timezone.localdate() + timedelta(days=1), is_dt)
        qs = Deals.objects.filter(**{f"{DATE_FIELD}__gte": s, f"{DATE_FIELD}__lt": e})

    sales_expr = ExpressionWrapper(F("buyer_price") * F("shipped_quantity"),
                                   output_field=DecimalField(max_digits=18, decimal_places=2))
    buy_expr   = ExpressionWrapper(F("supplier_price") * F("received_quantity"),
                                   output_field=DecimalField(max_digits=18, decimal_places=2))

    agg = qs.aggregate(
        sales=Coalesce(Sum(sales_expr), Decimal("0")),
        supplier=Coalesce(Sum(buy_expr), Decimal("0")),
        transport=Coalesce(Sum("transport_cost"), Decimal("0")),
        tonnage=Coalesce(Sum("shipped_quantity"), Decimal("0")),
        shipments=Coalesce(Count("id"), 0),
    )

    net = agg["sales"] - (agg["supplier"] + agg["transport"])
    mpt = (net / agg["tonnage"]) if agg["tonnage"] else Decimal("0")

    return {
        "net_profit":     float(round(net, 2)),
        "sales":          float(round(agg["sales"], 2)),
        "supplier_cost":  float(round(agg["supplier"], 2)),
        "transport_cost": float(round(agg["transport"], 2)),
        "margin_per_t":   float(round(mpt, 2)),
        "tonnage":        float(agg["tonnage"]),
        "shipments":      int(agg["shipments"]),
    }

def monthly_trends_data(months: int = 12) -> dict:
    """Агрегирует тренды за rolling-12: Net Profit, Supplier Cost, Transport $/t."""
    tz_now = timezone.now()
    start = tz_now.replace(day=1) - relativedelta(months=months - 1)

    # безопасные выражения для умножений (чтобы БД/ORM не ругались на типы)
    sales_expr = ExpressionWrapper(
        F('buyer_price') * F('shipped_quantity'),
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )
    supplier_expr = ExpressionWrapper(
        F('supplier_price') * F('received_quantity'),
        output_field=DecimalField(max_digits=18, decimal_places=2),
    )

    qs = Deals.objects.filter(date__gte=start, date__lt=tz_now)

    rows = (qs.annotate(m=TruncMonth('date'))
              .values('m')
              .annotate(
                  sales=Coalesce(Sum(sales_expr), Decimal('0')),
                  supplier=Coalesce(Sum(supplier_expr), Decimal('0')),
                  transport=Coalesce(Sum('transport_cost'), Decimal('0')),
                  tonnage=Coalesce(Sum('shipped_quantity'), Decimal('0')),
              )
              .order_by('m'))

    months_lbl, net_profit, supplier_cost, transport_per_t = [], [], [], []
    for r in rows:
        m = r['m']
        months_lbl.append(m.strftime('%b'))
        sales = r['sales'] or Decimal('0')
        supplier = r['supplier'] or Decimal('0')
        transport = r['transport'] or Decimal('0')
        tons = r['tonnage'] or Decimal('0')

        net = sales - (supplier + transport)
        net_profit.append(round(float(net), 2))
        supplier_cost.append(round(float(supplier), 2))
        tpt = float(transport) / float(tons) if tons else 0.0
        transport_per_t.append(round(tpt, 2))

    return {
        "months": months_lbl,
        "net_profit": net_profit,
        "supplier_cost": supplier_cost,
        "transport_per_t": transport_per_t,
        "currency": "CAD",
    }

# API-обёртка
def monthly_trends_api(request):
    return JsonResponse(monthly_trends_data(), safe=True)