# crm/ai_dashboard/logic/logistics.py

from decimal import Decimal, ROUND_HALF_UP

# 📦 Расчёт логистики за 1 тонну и за 1 тюк, сравнение с другими сделками

def analyze_logistics(deal, average_logistics=None):
    suggestions = []

    if not (deal.transport_cost and deal.shipped_quantity):
        return suggestions

    # 💰 Логистика за тонну
    try:
        per_ton_cost = (deal.transport_cost / deal.shipped_quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        suggestions.append(f"🚛 Логистика: {per_ton_cost} $/т")
    except (ZeroDivisionError, TypeError):
        per_ton_cost = None

    # 📦 Логистика за тюк (если есть количество тюков)
    if deal.shipped_pallets:
        try:
            per_bale_cost = (deal.transport_cost / deal.shipped_pallets).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            suggestions.append(f"📦 Логистика: {per_bale_cost} $/тюк")
        except (ZeroDivisionError, TypeError):
            pass

    # 🔍 Сравнение с средней логистикой (если передана)
    if average_logistics and per_ton_cost:
        diff = per_ton_cost - average_logistics
        if diff > Decimal('20.00'):
            suggestions.append(f"⚠️ Логистика выше средней на {diff} $/т")
        elif diff < Decimal('-20.00'):
            suggestions.append(f"✅ Логистика выгоднее средней на {-diff} $/т")

    return suggestions
