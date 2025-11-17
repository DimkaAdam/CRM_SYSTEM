from django.views.decorators.http import require_http_methods, require_GET
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.mail import EmailMessage
from django.conf import settings

from .models import (
    Company,
    CompanyEmail,
    EmailRecipientPreference,
    Employee,
)

import os
import json
import re


@require_GET
def api_company_emails(request, company_id: int):
    company = get_object_or_404(Company, pk=company_id)
    data = [
        {"id": e.id, "name": e.name or "", "email": e.email,
         "is_default": e.is_default, "active": e.active}
        for e in company.emails.filter(active=True).order_by('-is_default','name','email')
    ]
    return JsonResponse({"emails": data})

@require_http_methods(["POST"])
@transaction.atomic
def api_company_emails_add(request, company_id: int):
    company = get_object_or_404(Company, pk=company_id)
    name  = (request.POST.get("name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    is_default = request.POST.get("is_default") in ("1","true","True","on")

    if not email:
        return HttpResponseBadRequest("email is required")

    obj, created = CompanyEmail.objects.get_or_create(company=company, email=email, defaults={"name": name})
    if not created:
        # обновим имя, если прислали
        if name:
            obj.name = name
    if is_default:
        company.emails.update(is_default=False)
        obj.is_default = True
    obj.active = True
    obj.save()
    return JsonResponse({"ok": True, "id": obj.id})

@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def api_company_emails_delete(request, company_id: int, email_id: int):
    company = get_object_or_404(Company, pk=company_id)
    obj = get_object_or_404(CompanyEmail, pk=email_id, company=company)
    obj.active = False
    obj.is_default = False
    obj.save()
    return JsonResponse({"ok": True})


@require_GET
def api_get_email_prefs(request):
    """
    Возвращает сохранённый по умолчанию набор сотрудников для company+context.
    Ответ: {"selected_contact_ids": [1, 2, 3]}
    """
    company_id = request.GET.get("company_id")
    context = request.GET.get("context")

    if not company_id or not context:
        return HttpResponseBadRequest("company_id and context are required")

    pref = EmailRecipientPreference.objects.filter(
        company_id=company_id,
        context=context,
    ).first()

    if pref:
        ids = list(pref.employees.values_list("id", flat=True))
    else:
        ids = []

    return JsonResponse({"selected_contact_ids": ids})




@require_http_methods(["POST"])
@transaction.atomic
def api_send_report_email(request):
    """
    Отправка scale ticket по e-mail и АВТО-сохранение адресов
    в CompanyEmail для этой компании.
    """
    company_id = request.POST.get("company_id")
    subject = request.POST.get("subject", "(no subject)")
    body = request.POST.get("body", "")
    attachment_rel = request.POST.get("attachment_relative") or ""

    if not company_id:
        return HttpResponseBadRequest("company_id is required")

    company = get_object_or_404(Company, id=company_id)

    # 1) Берём emails, которые пришли одной строкой / JSON-массивом
    raw = request.POST.get("emails_raw") or ""
    emails = []
    if raw:
        try:
            # если фронт прислал JSON: ["a@b.com","c@d.com"]
            emails = json.loads(raw)
            if isinstance(emails, str):
                emails = [emails]
        except json.JSONDecodeError:
            # если прислали просто строку вида "a@b.com"
            emails = [raw]

    # 2) Плюс старый режим через contact_ids (если вдруг ещё используешь)
    ids_raw = request.POST.getlist("contact_ids[]") or request.POST.get("contact_ids")
    if ids_raw:
        if isinstance(ids_raw, str):
            try:
                ids = json.loads(ids_raw)
            except Exception:
                ids = []
        else:
            ids = ids_raw

        qs = CompanyEmail.objects.filter(company=company, id__in=ids, active=True)
        emails_from_ids = list(qs.values_list("email", flat=True))
        emails.extend(emails_from_ids)

    # 3) Нормализуем и убираем дубли
    clean = []
    for e in emails:
        if not e:
            continue
        e = e.strip()
        if e and e not in clean:
            clean.append(e)
    emails = clean

    if not emails:
        return HttpResponseBadRequest("No recipients")

    # 4) Гарантируем, что ВСЕ эти адреса сохранены в CompanyEmail
    existing = set(
        CompanyEmail.objects.filter(company=company, email__in=emails)
        .values_list("email", flat=True)
    )
    new_emails = [e for e in emails if e not in existing]

    for addr in new_emails:
        CompanyEmail.objects.create(company=company, email=addr)

    # 5) Собираем путь к PDF и отправляем письмо
    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=emails,
    )

    if attachment_rel:
        abs_path = os.path.join(
            settings.MEDIA_ROOT, "reports", "scale_tickets", attachment_rel
        )
        if not os.path.exists(abs_path):
            return HttpResponseBadRequest(f"Attachment not found: {attachment_rel}")
        msg.attach_file(abs_path)

    msg.send(fail_silently=False)

    return JsonResponse({"ok": True, "sent_to": emails})
@require_http_methods(["POST"])
@transaction.atomic
def api_save_email_prefs(request):
    company_id = request.POST.get("company_id")
    context = request.POST.get("context")
    ids_raw = request.POST.getlist("contact_ids[]") or request.POST.get("contact_ids")
    if not company_id or not context:
        return HttpResponseBadRequest("company_id and context are required")

    if isinstance(ids_raw, str):
        try:
            employee_ids = json.loads(ids_raw)
        except Exception:
            employee_ids = []
    else:
        employee_ids = ids_raw or []

    company = get_object_or_404(Company, id=company_id)
    pref, _ = EmailRecipientPreference.objects.get_or_create(company=company, context=context)

    employees = Employee.objects.filter(id__in=employee_ids, contact__company=company)
    pref.employees.set(employees)
    pref.save()

    return JsonResponse({"ok": True, "saved_ids": list(employees.values_list("id", flat=True))})


@require_http_methods(["GET"])
def api_company_contacts(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    qs = (
        Employee.objects
        .filter(contact__company_id=company.id)
        .exclude(email__isnull=True)
        .exclude(email__exact="")
        .order_by("name")
    )
    data = [{"id": e.id, "name": e.name or "", "email": e.email} for e in qs]
    return JsonResponse({"contacts": data})