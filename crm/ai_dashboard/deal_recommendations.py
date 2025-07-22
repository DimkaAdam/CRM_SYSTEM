# crm/ai_dashboard/deal_recommendations.py
from datetime import datetime
from ..models import Deals, ContactMaterial,TruckProfile
from django.db.models import F
from .transport import suggest_transport_adjustments
from math import ceil
from django.utils.timezone import make_aware

def analyze_deals():
    now = datetime.now()
    start_of_month = make_aware(datetime(now.year, now.month, 1))

    # Фильтруем только сделки этого месяца и убыточные
    problem_deals = Deals.objects.filter(
        total_income_loss__lt=0,
        date__gte=start_of_month
    )
    recommendations = []

    for deal in problem_deals:
        rec = {
            "deal_id": deal.id,
            "company": deal.supplier.name if deal.supplier else "Unknown",
            "grade": deal.grade,
            "income_loss": round(deal.total_income_loss, 2),
            "shipped_quantity": deal.shipped_quantity,
            "bales": deal.shipped_pallets,
            "date": deal.date.strftime("%d.%m.%Y") if deal.date else "неизвестно",
            "suggestions": []
        }

        # ❗️Проверка на критически некорректные данные
        if not deal.shipped_quantity or not deal.received_quantity:
            rec["status"] = "error"
            rec["analysis"] = "⚠️ Hmm... shipped or received quantity is zero. Please double-check the data"
            rec["suggestions"].append("⚠️ Оппа, Error in the calculation, check data.")
            recommendations.append(rec)
            continue

        # 💰 Расчёт безубыточного объёма — если есть все данные

        try:
            buyer_price = float(deal.buyer_price)
            supplier_price = float(deal.supplier_price)
            transport_cost = float(deal.transport_cost)
            shipped_quantity = float(deal.shipped_quantity)
            received_quantity = float(deal.received_quantity)

            # 💡 Коэффициент приёмки (waste ratio)
            if shipped_quantity == 0:
                raise ZeroDivisionError("shipped_quantity = 0")

            waste_ratio = received_quantity / shipped_quantity

            denominator = buyer_price - (supplier_price * waste_ratio)
            if denominator == 0:
                raise ZeroDivisionError("Деление на 0 в расчёте break-even")

            break_even_shipped_qty = round(transport_cost / denominator, 2)

            rec["suggestions"].append(
                f"📈 Нужно минимум {break_even_shipped_qty} тонн для выхода в 0 (учтён приём по {round(waste_ratio * 100)}%)."
            )
        except ZeroDivisionError:
            rec["suggestions"].append("⚠️ Деление на 0 при расчёте точки безубыточности.")
        except Exception as e:
            rec["suggestions"].append(f"⚠️ Ошибка при расчёте break-even: {str(e)}")

        # 📦 2. Малая отгрузка — только если маржа > 0
        truck = None
        if deal.transport_company:
            truck = TruckProfile.objects.filter(company=deal.transport_company).first()

        if truck:
            avg_bale_weight = get_avg_bale_weight(truck.company, deal.grade)
            if avg_bale_weight and avg_bale_weight < 250:
                max_stack = truck.max_spots * 2
            else:
                max_stack = truck.max_spots
            min_required_bales = max_stack - 2# 🔧 можно +/- менять как хочешь
        else:
            min_required_bales = 6  # дефолт если трак не указан

        if deal.shipped_pallets and deal.shipped_pallets < min_required_bales:
            rec["suggestions"].append(
                f"🚛 Отгрузка слишком малая ({deal.shipped_pallets} тюков). Желательно минимум {min_required_bales} под текущий трак."
            )
            # ❗️Пропускаем расчёт break-even, если уже остановили анализ из-за малой отгрузки
            if rec.get("status") != "skip":
                if deal.buyer_price and deal.supplier_price and deal.transport_cost:
                    try:
                        margin_per_ton = deal.buyer_price - deal.supplier_price - deal.transport_cost
                        if margin_per_ton > 0:
                            break_even_qty = round(-deal.total_income_loss / margin_per_ton, 2)
                            rec["suggestions"].append(
                                f"📈 Нужно минимум {break_even_qty} тонн для выхода в 0."
                            )
                        else:
                            rec["suggestions"].append(
                                f"📉 Нет наценки: продажа = ${deal.buyer_price}/т, закупка = ${deal.supplier_price}/т, "
                                f"логистика = ${deal.transport_cost} → итоговая маржа = ${round(margin_per_ton, 2)}/т.\n"
                                f"🔻 Убыток неизбежен — увеличение объёма не поможет."
                            )
                    except ZeroDivisionError:
                        rec["suggestions"].append("⚠️ Деление на 0 при расчёте безубыточности.")
                    except Exception as e:
                        rec["suggestions"].append(f"⚠️ Ошибка при расчёте: {str(e)}")

            # 🛑 Прерываем дальнейший анализ
            rec["status"] = "skip"
            rec["analysis"] = "Недостаточно тюков под этот трак. Увеличь количество, остальной анализ неактуален."
            recommendations.append(rec)
            continue

        # 🚚 3. Анализ логистики на основе профиля траков
        truck_result = suggest_truck_optimization(deal)

        if truck_result:
            rec["status"] = "better_truck"
            rec["analysis"] = "Найдены более выгодные варианты логистики на основе траков."
            for suggestion in truck_result:
                rec["suggestions"].append("🚛 " + suggestion["message"])


        # 🔄 4. Альтернатива по поставщику
        other_suppliers = ContactMaterial.objects.filter(
            material=deal.grade
        ).exclude(contact__company=deal.supplier).order_by("price")[:1]

        if other_suppliers.exists():
            cheaper = other_suppliers[0]
            if cheaper.price < deal.supplier_price:
                delta = round(deal.supplier_price - cheaper.price, 2)
                rec["suggestions"].append(
                    f"🏷 Поставщик {cheaper.contact.company.name} поставляет дешевле на ${delta}/тонну. Попробуй снизить цену."
                )

        # 📊 5. Подключение анализа логистики
        transport_result = suggest_transport_adjustments(deal)
        rec["status"] = transport_result["status"]
        rec["analysis"] = transport_result["message"]

        for suggestion in transport_result["suggestions"]:
            rec["suggestions"].append("🔧 " + suggestion["message"])

        recommendations.append(rec)

    return recommendations

from django.db.models import Avg, F, FloatField, ExpressionWrapper

def get_avg_bale_weight(company, grade):
    deals = Deals.objects.filter(
        transport_company=company,
        grade=grade,
        shipped_quantity__gt=0,
        shipped_pallets__gt=0
    ).annotate(
        bale_weight=ExpressionWrapper(
            F('shipped_quantity') * 1000 / F('shipped_pallets'),
            output_field=FloatField()
        )
    )
    avg = deals.aggregate(avg=Avg('bale_weight'))['avg']
    return round(avg, 2) if avg else None

import math
def suggest_truck_optimization(deal):
    suggestions = []

    if not (deal.shipped_quantity and deal.shipped_pallets and deal.transport_cost):
        return suggestions

    current_cost_per_ton = deal.transport_cost
    shipped_qty = float(deal.shipped_quantity)
    shipped_bales = int(deal.shipped_pallets)
    total_weight = shipped_qty * 1000  # в кг

    trucks = TruckProfile.objects.all()
    cheaper_options = []

    for truck in trucks:
        if truck.base_cost == 0:
            continue

        bale_weight = get_avg_bale_weight(truck.company, deal.grade)  # ✅ динамически
        if not bale_weight:
            continue

        max_tons = truck.max_tons
        max_spots = truck.max_spots

        # 👇 Определяем можно ли делать double stack
        if bale_weight < 250:
            stacking_allowed = True
            max_bales = min(
                math.floor((max_tons * 1000) / bale_weight),
                max_spots * 2
            )
        else:
            stacking_allowed = False
            max_bales = min(
                math.floor((max_tons * 1000) / bale_weight),
                max_spots
            )

        # 🚫 Пропускаем, если не влезает по весу или кол-ву палет
        if shipped_bales > max_bales or total_weight > max_tons * 1000:
            continue

        if shipped_bales < max_bales:
            needed_bales = max_bales
            needed_tons = round((bale_weight * max_bales) / 1000, 2)
            message = (
                f"⏳ Выгода будет при полной загрузке {truck.company.name}: "
                f"{needed_bales} тюков / ~{needed_tons} тонн. "
                f"Тогда логистика составит ${round((truck.base_cost / needed_tons), 2)}/т"
            )
            suggestions.append({
                "action": "wait_accumulate",
                "truck": truck.company.name,
                "needed_bales": needed_bales,
                "message": message
            })
            continue

        # ✅ Считаем логистику
        trips = ceil(shipped_bales / max_bales)
        total_logistics_cost = truck.base_cost * trips
        if shipped_qty == 0:
            continue  # пропускаем, деление на 0
        new_cost_per_ton = round(total_logistics_cost / shipped_qty, 2)

        if new_cost_per_ton < current_cost_per_ton:
            cheaper_options.append((truck, new_cost_per_ton, stacking_allowed))

    if cheaper_options:
        best_truck, best_price, stacking = sorted(cheaper_options, key=lambda x: x[1])[0]
        message = f"🚚 Рекомендуется {best_truck.company.name} — логистика ${best_price}/т (вместо ${current_cost_per_ton}/т)"
        if stacking:
            message += " с double stack"
        suggestions.append({
            "action": "truck_swap",
            "truck": best_truck.company.name,
            "company": best_truck.company.name,
            "new_logistics_price": best_price,
            "message": message
        })

    return suggestions


from django.db.models import Sum, Count, F

def analyze_scale_ticket_groups():
    tickets = (
        Deals.objects
        .filter(scale_ticket__isnull=False)
        .values("scale_ticket")
        .annotate(
            total_deals=Count("id"),
            total_amount=Sum("buyer_price" * F("shipped_quantity")),
            supplier_total=Sum("supplier_price" * F("received_quantity")),
            total_transport=Sum("transport_cost"),
            total_shipped=Sum("shipped_quantity"),
            total_bales=Sum("shipped_pallets")
        )
    )

    insights = []

    for t in tickets:
        income = (t["total_amount"] or 0) - (t["supplier_total"] or 0) - (t["total_transport"] or 0)
        if income >= 0:
            continue

        ticket_deals = Deals.objects.filter(scale_ticket=t["scale_ticket"])
        transport_company = ticket_deals.first().transport_company if ticket_deals.exists() else None

        insight = {
            "scale_ticket": t["scale_ticket"],
            "total_deals": t["total_deals"],
            "shipped_tons": round(t["total_shipped"], 2) if t["total_shipped"] else 0,
            "bales": t["total_bales"] or 0,
            "income_loss": round(income, 2),
            "suggestions": []
        }

        # 💡 Малая суммарная отгрузка
        if insight["bales"] < 6:
            insight["suggestions"].append(
                f"📦 Общая отгрузка слишком малая: {insight['bales']} тюков. Желательно >= 6."
            )

        # 🚚 Альтернатива по транспорту
        if transport_company:
            fake_deal = ticket_deals.first()
            fake_deal.shipped_quantity = t["total_shipped"]
            fake_deal.shipped_pallets = t["total_bales"]
            truck_suggestions = suggest_truck_optimization(fake_deal)

            if truck_suggestions:
                for s in truck_suggestions:
                    insight["suggestions"].append("🚛 " + s["message"])
            else:
                insight["suggestions"].append(
                    f"💡 Нет более выгодного трака, чем {transport_company.name}."
                )

        insights.append(insight)

    return insights