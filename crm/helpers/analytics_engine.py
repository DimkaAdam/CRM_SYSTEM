from datetime import date
from calendar import monthrange

from django.db.models import Sum, Count, DecimalField, ExpressionWrapper, F
from django.db.models.functions import Coalesce
from crm.models import Deals


# ============================================================
# This helper calculates KPI for the current month up to today
# and compares them with the same period last month, returning
# ready-to-use figures for all CRM sections.
# ============================================================

def current_month_range_until_today():
    """
    Range: 1st day of current month → today
    """
    today = date.today()
    start = today.replace(day=1)
    end = today
    return start, end


def prev_month_range_until_same_day():
    """
    Range: 1st day of previous month → same day number in previous month,
    or last day (if today > number of days in previous month)
    """
    today = date.today()

    if today.month == 1:
        prev_year = today.year - 1
        prev_month = 12
    else:
        prev_year = today.year
        prev_month = today.month - 1

    days_in_prev_month = monthrange(prev_year, prev_month)[1]
    end_day = min(today.day, days_in_prev_month)

    start = date(prev_year, prev_month, 1)
    end = date(prev_year, prev_month, end_day)

    return start, end


# ============================================================
# DEALS AGGREGATIONS
# ============================================================

def aggregate_deals_range(start_date, end_date):
    """
    Returns aggregates:
    net_profit, sales, supplier_cost, transport_cost, tonnage, shipments
    """
    qs = Deals.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )

    # Define safe expressions with explicit output_field
    sales_expr = ExpressionWrapper(
        F('buyer_price') * F('shipped_quantity'),
        output_field=DecimalField(max_digits=18, decimal_places=2)
    )

    supplier_expr = ExpressionWrapper(
        F('supplier_price') * F('received_quantity'),
        output_field=DecimalField(max_digits=18, decimal_places=2)
    )

    res = qs.aggregate(
        net_profit=Coalesce(Sum('total_income_loss'), 0),
        sales=Coalesce(Sum(sales_expr), 0),
        supplier_cost=Coalesce(Sum(supplier_expr), 0),
        transport_cost=Coalesce(Sum('transport_cost'), 0),
        tonnage=Coalesce(Sum('shipped_quantity'), 0),
        shipments=Coalesce(Count('id'), 0),
    )

    # Convert to Python types
    return {
        "net_profit": float(res['net_profit'] or 0),
        "sales": float(res['sales'] or 0),
        "supplier_cost": float(res['supplier_cost'] or 0),
        "transport_cost": float(res['transport_cost'] or 0),
        "tonnage": float(res['tonnage'] or 0),
        "shipments": int(res['shipments'] or 0),
    }


# ============================================================
# FINAL KPI FOR DASHBOARD
# ============================================================

def compute_period_kpi():
    """
    Main function.
    Calculates KPI for:
      • current month (1 → today)
      • same period last month
    Returns a dictionary that can be sent to template or API.
    """

    # --- date ranges ---
    cur_start, cur_end = current_month_range_until_today()
    prev_start, prev_end = prev_month_range_until_same_day()

    # --- aggregates ---
    cur = aggregate_deals_range(cur_start, cur_end)
    prev = aggregate_deals_range(prev_start, prev_end)

    # --- profit ---
    cur_np = cur["net_profit"]
    prev_np = prev["net_profit"]

    if prev_np == 0:
        net_pct = None
    else:
        net_pct = (cur_np - prev_np) / abs(prev_np) * 100.0

    # --- margin per ton ---
    ton = cur["tonnage"]
    if ton > 0:
        margin = cur_np / ton
    else:
        margin = 0

    # --- final KPI ---
    return {
        # current values
        "net_profit": cur_np,
        "sales": cur["sales"],
        "supplier_cost": cur["supplier_cost"],
        "transport_cost": cur["transport_cost"],
        "tonnage": cur["tonnage"],
        "shipments": cur["shipments"],
        "margin_per_t": round(margin, 2),

        # previous period
        "net_profit_prev": prev_np,

        # % change
        "net_profit_change_pct": round(net_pct, 1) if net_pct is not None else None,

        # date ranges (can be used for labels)
        "current_period": (cur_start, cur_end),
        "previous_period": (prev_start, prev_end),
    }

# ============================================================
# end
# ============================================================