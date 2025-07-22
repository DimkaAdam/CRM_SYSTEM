from datetime import datetime, timedelta
from crm.models import Company, Deals

INACTIVITY_DAYS_THRESHOLD = 30  # можно менять


def find_inactive_clients():
    today = datetime.today().date()
    buyers = Company.objects.filter(contacts__company_type='buyers').distinct()

    inactive_clients = []

    for buyer in buyers:
        last_deal = Deals.objects.filter(buyer=buyer).order_by('-date').first()
        if last_deal:
            days_since_last = (today - last_deal.date.date()).days
        else:
            days_since_last = 9999  # никогда не отгружали

        if days_since_last >= INACTIVITY_DAYS_THRESHOLD:
            inactive_clients.append({
                'company': buyer,
                'days_since': days_since_last,
                'last_deal': last_deal
            })

    return inactive_clients
