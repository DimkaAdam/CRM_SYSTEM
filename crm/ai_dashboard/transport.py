# crm/ai_dashboard/transport.py

def suggest_transport_adjustments(deal):
    """
    Анализирует убыточную сделку и предлагает способы компенсировать убыток:
    - повысить цену продажи
    - снизить цену закупки
    - занизить вес (received_quantity, до 30%)
    - комбинированный вариант
    """

    buyer_price = float(deal.buyer_price)
    supplier_price = float(deal.supplier_price)
    shipped_quantity = float(deal.shipped_quantity)
    received_quantity = float(deal.received_quantity)
    transport_cost = float(deal.transport_cost)

    suggestions = []

    # 1. Текущая прибыль
    current_profit = (buyer_price * shipped_quantity) - (supplier_price * received_quantity) - transport_cost
    if current_profit >= 0:
        return {"status": "✅ Profit", "message": "Сделка прибыльна", "suggestions": []}

    # 2. Минимальная цена продажи
    if shipped_quantity != 0:
        min_required_buyer_price = round(((supplier_price * received_quantity) + transport_cost) / shipped_quantity, 2)
        suggestions.append({
            "action": "increase_buyer_price",
            "required_price": min_required_buyer_price,
            "message": f"Min sell price: ${min_required_buyer_price}/т"
        })
    else:
        suggestions.append({
            "action": "increase_buyer_price",
            "message": "⚠️ Невозможно рассчитать цену продажи — shipped_quantity = 0"
        })

    # 3. Максимальная закупочная цена
    if received_quantity != 0:
        max_allowed_supplier_price = round(((buyer_price * shipped_quantity) - transport_cost) / received_quantity, 2)
        if max_allowed_supplier_price < 0:
            max_allowed_supplier_price = 0
            supplier_comment = "free"
        else:
            supplier_comment = f"${max_allowed_supplier_price}/т"

        suggestions.append({
            "action": "decrease_supplier_price",
            "allowed_price": max_allowed_supplier_price,
            "message": f"Max supplier price: {supplier_comment}"
        })

    else:
        suggestions.append({
            "action": "decrease_supplier_price",
            "message": "⚠️ Невозможно рассчитать цену закупки — received_quantity = 0"
        })

    # 4. Занижение веса (received_quantity)
    max_reduction = received_quantity * 0.3
    min_received = received_quantity - max_reduction
    test_received = received_quantity
    step = 0.1
    reduction_found = False
    reduction_percent = 0
    covered_by_reduction = 0

    while test_received >= min_received:
        test_supplier_total = supplier_price * test_received
        test_profit = (buyer_price * shipped_quantity) - (test_supplier_total + transport_cost)
        if test_profit >= 0:
            reduction_found = True
            reduction_percent = round((1 - test_received / received_quantity) * 100, 1)
            covered_by_reduction = (supplier_price * received_quantity) - test_supplier_total
            suggestions.append({
                "action": "reduce_received_quantity",
                "suggested_quantity": round(test_received, 2),
                "reduction_percent": reduction_percent,
                "message": f"Можно выйти в ноль, если занижать received до {round(test_received, 2)} т (-{reduction_percent}%)"
            })
            break
        test_received -= step

    # 5. Комбинированное решение (если занижение не покрывает весь убыток)
    loss = abs(current_profit)
    max_reduction_percent = 30
    best_combination = None

    for reduction in range(1, max_reduction_percent + 1):
        reduced_received_quantity = received_quantity * (1 - reduction / 100)
        supplier_total = supplier_price * reduced_received_quantity
        covered = (supplier_price * received_quantity) - supplier_total
        remaining_loss = loss - covered
        supplier_adjustment = remaining_loss / 2
        buyer_adjustment = remaining_loss / 2

        try:
            adjusted_supplier_price = round(supplier_price - (supplier_adjustment / reduced_received_quantity), 2)
        except ZeroDivisionError:
            adjusted_supplier_price = float('inf')

        try:
            adjusted_buyer_price = round(buyer_price + (buyer_adjustment / shipped_quantity), 2)
        except ZeroDivisionError:
            adjusted_buyer_price = float('inf')

        if covered >= loss:
            supplier_comment = f"${adjusted_supplier_price}/т" if adjusted_supplier_price >= 0 else "free"
            buyer_comment = f"${adjusted_buyer_price}/т" if adjusted_buyer_price < float('inf') else "н/д"

            best_combination = {
                "reduce_received_quantity_to": round(reduced_received_quantity, 2),
                "new_supplier_price": max(adjusted_supplier_price, 0),
                "new_buyer_price": adjusted_buyer_price,
                "message": (
                    f"Combo: reduce weight to {round(reduced_received_quantity, 2)} т (-{reduction}%), "
                    f"supplier = {supplier_comment}, buyer = {buyer_comment}"
                )
            }
            break
        else:
            best_combination = {
                "reduce_received_quantity_to": round(reduced_received_quantity, 2),
                "new_supplier_price": adjusted_supplier_price,
                "new_buyer_price": adjusted_buyer_price,
                "message": f"Combo: reduce weight to {round(reduced_received_quantity, 2)} т (-{reduction}%), supplier = ${adjusted_supplier_price}/т, buyer = ${adjusted_buyer_price}/т"
            }

    if best_combination:
        suggestions.append({"action": "combined_strategy", **best_combination})

    return {
        "status": "❌ Loss",
        "message": "Сделка убыточна. Ниже варианты для выхода в ноль.",
        "suggestions": suggestions
    }


