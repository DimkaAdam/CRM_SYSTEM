from crm.models import Deals
from collections import defaultdict
from datetime import timedelta, date
import statistics

def predict_shipments():
    supplier_deals = defaultdict(list)
    predictions = []


    # 🔍 Сбор всех сделок по поставщикам, упорядочим по дате
    for deal in Deals.objects.filter(supplier__isnull=False).exclude(date=None).order_by("date"):
        supplier_deals[deal.supplier].append(deal.date.date())  # date → datetime.date

    for supplier, dates in supplier_deals.items():
        # 📆 Удалим дубликаты и отсортируем
        unique_dates = sorted(list(set(dates)))

        if len(unique_dates) < 3:
            continue  # недостаточно данных

        # 📈 Вычисляем интервалы
        deltas = [
            (unique_dates[i] - unique_dates[i - 1]).days
            for i in range(1, len(unique_dates))
        ]
        avg_interval = round(statistics.mean(deltas))
        last_date = unique_dates[-1]
        predicted_date = last_date + timedelta(days=avg_interval)

        # 🧪 Лог для отладки
        print(f"📦 {supplier.name}: Last = {last_date}, Avg = {avg_interval}d, Next = {predicted_date}")

        # 📅 Только если дата близка (в пределах 14 дней)
        if predicted_date <= date.today() + timedelta(days=14):
            predictions.append({
                "supplier": supplier.name,
                "last_date": last_date,
                "predicted_date": predicted_date,
                "avg_interval": avg_interval
            })

    predictions.sort(key=lambda x: x['predicted_date'])

    return predictions
