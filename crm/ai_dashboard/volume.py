# crm/ai_dashboard/volume.py

def calculate_breakeven_weight(buyer_price, supplier_price, logistics_cost_per_ton, fixed_logistics_cost=0):
    """
    Рассчитывает точку безубыточности в тоннах (вес, необходимый для покрытия всех затрат)

    :param buyer_price: Цена продажи ($/тонна)
    :param supplier_price: Цена закупки ($/тонна)
    :param logistics_cost_per_ton: Стоимость логистики на тонну ($)
    :param fixed_logistics_cost: Фиксированные логистические расходы ($)
    :return: Необходимый вес (тонн) для выхода в ноль, либо None, если сделка убыточна при любом объеме
    """
    profit_per_ton = buyer_price - supplier_price - logistics_cost_per_ton  # 💰 Прибыль с 1 тонны

    if profit_per_ton <= 0:
        return None  # ❌ Сделка всегда убыточна

    breakeven_weight = fixed_logistics_cost / profit_per_ton  # ⚖️ Вес для выхода в ноль
    return round(breakeven_weight, 2)
