from datetime import datetime, timedelta
from crm.models import Company, Deals

INACTIVITY_DAYS_THRESHOLD = 30  # можно менять

def find_inactive_clients():
    today = datetime.today().date()
    suppliers = Company.objects.filter(contacts__company_type='suppliers').distinct()  # ✅ ищем поставщиков

    inactive_clients = []

    for supplier in suppliers:
        last_deal = Deals.objects.filter(supplier=supplier).order_by('-date').first()  # ✅ сделки по поставщику
        if last_deal:
            days_since_last = (today - last_deal.date.date()).days
        else:
            days_since_last = 9999  # никогда не было сделок

        if days_since_last >= INACTIVITY_DAYS_THRESHOLD:
            inactive_clients.append({
                'company': supplier,
                'days_since': days_since_last,
                'last_deal': last_deal
            })

    return inactive_clients
