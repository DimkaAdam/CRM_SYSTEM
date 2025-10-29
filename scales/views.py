from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import ReceivedMaterial
import json
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import openpyxl
from openpyxl.styles import Alignment, Font
from io import BytesIO
from .utils import business_day
from datetime import timedelta
from django.http import HttpResponse
from datetime import datetime


@login_required
def home(request):
    return render(request, "scales/home.html", {  # ← ВАЖНО: .html
        "title": "Scales • Home",
    })

@login_required
@require_http_methods(["GET"])
def api_list_received(request):
    # отдаём строки только выбранной компании
    company = request.session.get("company_slug")
    qs = ReceivedMaterial.objects.filter(company_slug=company).order_by("-created_at")[:500]
    data = [
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "material": r.material,
            "gross": float(r.gross_kg),
            "net": float(r.net_kg),
            "supplier": r.supplier,
            "tag": r.tag,
        }
        for r in qs
    ]
    return JsonResponse({"items": data})

@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_create_received(request):
    # принимаем JSON: {material, gross, net, supplier, tag}
    body = json.loads(request.body.decode("utf-8"))
    company = request.session.get("company_slug") or "unknown"
    item = ReceivedMaterial.objects.create(
        material  = body["material"].strip(),
        gross_kg  = Decimal(str(body["gross"])),
        net_kg    = Decimal(str(body["net"])),
        supplier  = body["supplier"].strip(),
        tag       = str(body["tag"]).strip(),
        company_slug = company,
        created_by = request.user if request.user.is_authenticated else None,
    )
    return JsonResponse({"ok": True, "id": item.id})
@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_update_received(request, pk):
    company = request.session.get("company_slug")
    obj = get_object_or_404(ReceivedMaterial, pk=pk, company_slug=company)
    body = json.loads(request.body.decode("utf-8"))

    # безопасно обновим поля
    obj.material = body.get("material", obj.material).strip()
    obj.gross_kg = Decimal(str(body.get("gross", obj.gross_kg)))
    obj.net_kg   = Decimal(str(body.get("net", obj.net_kg)))
    obj.supplier = body.get("supplier", obj.supplier).strip()
    obj.tag      = str(body.get("tag", obj.tag)).strip()
    obj.save()

    return JsonResponse({
        "ok": True,
        "item": {
            "id": obj.id, "date": obj.date.isoformat(),
            "material": obj.material, "gross": float(obj.gross_kg),
            "net": float(obj.net_kg), "supplier": obj.supplier, "tag": obj.tag
        }
    })

@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_delete_received(request, pk):
    company = request.session.get("company_slug")
    obj = get_object_or_404(ReceivedMaterial, pk=pk, company_slug=company)
    obj.delete()
    return JsonResponse({"ok": True})




@login_required
def export_daily_pdf(request):
    """
    Daily Material Report (Scales) — PDF с пагинацией.
    ?date=YYYY-MM-DD (по умолчанию сегодня).
    """
    # ===== Локальные импорты для PDF =====
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from django.conf import settings
    import os

    # ===== Входные =====
    company_slug = request.session.get("company_slug") or "unknown"
    company_name = request.session.get("company_name") or company_slug
    date_str = request.GET.get("date") or datetime.now().strftime("%Y-%m-%d")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

    # ===== Данные =====
    qs = (ReceivedMaterial.objects
          .filter(company_slug=company_slug, date=date_obj)
          .order_by("created_at"))

    # Основная таблица
    data = [["Material", "Gross (kg)", "Net (kg)", "Supplier", "Tag #"]]

    total_net = 0.0

    # Сводки
    by_material = {}            # {"CB": {"gross":..., "net":..., "count":...}, ...}
    by_supplier_mat = {}        # {"Inno Food": {"CB": {"gross":..., "net":...}, "_subtotal": {...}}, ...}

    for r in qs:
        g = float(r.gross_kg)
        n = float(r.net_kg)

        data.append([
            r.material,
            f"{g:.1f}",
            f"{n:.1f}",
            r.supplier,
            str(r.tag),
        ])

        total_net += n

        # — по материалу (общая сводка)
        bucket = by_material.setdefault(r.material, {"gross": 0.0, "net": 0.0, "count": 0})
        bucket["gross"] += g
        bucket["net"] += n
        bucket["count"] += 1

        # — по поставщику и материалу
        sup_map = by_supplier_mat.setdefault(r.supplier, {})
        mat_map = sup_map.setdefault(r.material, {"gross": 0.0, "net": 0.0})
        mat_map["gross"] += g
        mat_map["net"] += n
        # подсумма по поставщику
        st = sup_map.setdefault("_subtotal", {"gross": 0.0, "net": 0.0})
        st["gross"] += g
        st["net"] += n

    # ===== PDF init =====
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    PAGE_W, PAGE_H = A4

    # Поля и ширина
    M_L, M_R, M_T, M_B = 30, 30, 40, 40
    usable_w = PAGE_W - M_L - M_R

    # Лого
    logo_path = os.path.join(settings.BASE_DIR, 'crm', 'static', 'crm', 'images', 'logo3.png')

    # ===== Хелперы =====
    def draw_header():
        y = PAGE_H - 60
        if os.path.exists(logo_path):
            pdf.drawImage(ImageReader(logo_path), M_L, y - 50, width=70, height=70, mask='auto')

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(PAGE_W / 2, y, "Daily Material Report")

        pdf.setFont("Helvetica-Bold", 11)
        pdf.setFillColor(colors.darkblue)
        pdf.drawRightString(PAGE_W - M_R, y, company_name)

        pdf.setFont("Helvetica", 9)
        pdf.setFillColor(colors.HexColor("#555555"))
        pdf.drawRightString(PAGE_W - M_R, y - 14, f"Date: {date_obj.strftime('%d %b %Y')}")
        pdf.setStrokeColor(colors.HexColor("#aaaaaa"))
        pdf.setLineWidth(0.5)
        pdf.line(M_L, y - 50, PAGE_W - M_R, y - 50)
        return PAGE_H - 135

    def table_style():
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ])

    def ensure_space_or_new_page(y_cur, need=40):
        if y_cur - need < M_B:
            pdf.showPage()
            return draw_header()
        return y_cur

    def draw_table_paginated(all_rows, start_y, col_widths):
        header = all_rows[0]
        rows = all_rows[1:]
        i, y_cur = 0, start_y
        while i < len(rows):
            # бинарный поиск вместимости
            low, high, fit = 1, len(rows) - i, 0
            while low <= high:
                mid = (low + high) // 2
                trial = [header] + rows[i:i+mid]
                t_try = Table(trial, colWidths=col_widths)
                t_try.setStyle(table_style())
                _, h_try = t_try.wrap(usable_w, 0)
                if y_cur - h_try >= M_B:
                    fit = mid
                    low = mid + 1
                else:
                    high = mid - 1

            if fit == 0:
                pdf.showPage()
                y_cur = draw_header()
                continue

            chunk = [header] + rows[i:i+fit]
            t = Table(chunk, colWidths=col_widths)
            t.setStyle(table_style())
            w, h = t.wrap(usable_w, 0)
            x = M_L + (usable_w - w) / 2
            t.drawOn(pdf, x, y_cur - h)
            y_cur -= h + 10
            i += fit

            if i < len(rows) and y_cur < M_B + 60:
                pdf.showPage()
                y_cur = draw_header()
        return y_cur

    # ===== 1) Основная таблица =====
    y = draw_header()
    y = draw_table_paginated(data, y - 10, col_widths=[70, 110, 80, 80, 140, 80])

    # ===== 2) Общие итоги по дню =====

    for supplier in sorted(by_supplier_mat.keys()):
        mat_map = by_supplier_mat[supplier]
        print(f'{supplier}:')

        for mat in sorted([k for k in mat_map.keys() if k != '_subtotal']):
            val = mat_map[mat]['net']

            print(f'    {mat}- {val: .1f} kg;')
    y -= 40
    y = ensure_space_or_new_page(y, need=40)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(M_L, y, f"{supplier}:")
    y -= 14
    for mat in sorted([k for k in mat_map.keys() if k != '_subtotal']):
        val = mat_map[mat]["net"]
        pdf.drawString(M_L + 20, y, f"{mat} - {val:.1f} kg;")
        y -= 14

    # ===== Вывод =====
    pdf.save()
    buffer.seek(0)
    resp = HttpResponse(buffer, content_type="application/pdf")
    filename = f"Scales_Daily_{company_slug}_{date_obj.strftime('%Y-%m-%d')}.pdf"
    resp["Content-Disposition"] = f'attachment; filename=\"{filename}\"'
    return resp




@login_required
def export_monthly_excel(request):
    """Excel отчёт за месяц (по текущей компании)."""
    company = request.session.get("company_slug")
    month_str = request.GET.get("month")  # формат YYYY-MM
    if not month_str:
        month_str = datetime.now().strftime("%Y-%m")
    year, month = map(int, month_str.split("-"))

    records = ReceivedMaterial.objects.filter(
        company_slug=company,
        date__year=year,
        date__month=month
    ).order_by("date")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Monthly Report"

    ws.append(["Date", "Material", "Gross (kg)", "Net (kg)", "Supplier", "Tag #"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    total_gross = total_net = 0
    for r in records:
        ws.append([r.date.strftime("%Y-%m-%d"), r.material, float(r.gross_kg), float(r.net_kg), r.supplier, r.tag])
        total_gross += float(r.gross_kg)
        total_net += float(r.net_kg)

    ws.append([])
    ws.append(["Totals", "", total_gross, total_net, "", ""])
    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True)

    # автоширина
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"monthly_report_{company}_{month_str}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def home(request):
    is_manager = request.session.get("user_role") == "managers"  # <-- строго 'managers'
    return render(request, "scales/home.html", {"is_manager": is_manager})

def scales_home(request):
    today_bd = business_day()
    prev_bd = today_bd - timedelta(days=1)

    received_today = ReceivedMaterial.objects.filter(report_day=today_bd)
    received_prev  = ReceivedMaterial.objects.filter(report_day=prev_bd)

    return render(request, "scales/home.html", {
        "today_bd": today_bd,
        "prev_bd": prev_bd,
        "received_today": received_today,
        "received_prev": received_prev,
    })