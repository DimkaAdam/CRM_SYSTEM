from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlencode
from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import check_password
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import PortalCompany

def choose_company(request):
    companies = PortalCompany.objects.filter(is_active=True)
    return render(request, "entry_portal/choose_company.html", {"companies": companies})


@require_http_methods(["GET", "POST"])
def company_login(request):
    """
    Простой логин по 'общему паролю компании'.
    - Берём company_slug из сессии
    - Сверяем введённый пароль с company.shared_password (check_password)
    - Если ок → создаём/находим сервисного пользователя для этой компании и login()
    """
    slug = request.session.get("company_slug")
    name = request.session.get("company_name")
    target = request.GET.get("next") or request.session.get("company_target") or "/"

    if not slug:
        # Компания не выбрана — откатываем на экран выбора
        return redirect("/")

    company = get_object_or_404(PortalCompany, slug=slug, is_active=True)

    error = None
    if request.method == "POST":
        password = request.POST.get("password", "").strip()
        if not company.shared_password:
            error = "Пароль для этой компании не задан. Обратитесь к администратору."
        elif check_password(password, company.shared_password):
            # Создаём/находим сервисного пользователя для этой компании
            User = get_user_model()
            username = f"company__{company.slug}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"is_active": True}
            )
            # Пароль у этого пользователя не используется — вход по company_password
            if created and hasattr(user, "set_unusable_password"):
                user.set_unusable_password()
                user.save(update_fields=["password"])

            # Логиним
            login(request, user)

            # На всякий — сохраним удобный “ярлык” для шапки
            request.session["company_slug"] = company.slug
            request.session["company_name"] = company.name
            request.session["company_target"] = target

            return redirect(target)
        else:
            error = "Неверный пароль."

    return render(
        request,
        "entry_portal/company_login.html",
        {
            "title": f"Вход в {name or slug}",
            "company": {"slug": slug, "name": name},
            "next": target,
            "error": error,
        }
    )

TARGETS = {
    "pmb-depot": "/scales/home/",
    "local-to-global": "/crm/deals/",
}

def portal_login(request, slug):
    company = get_object_or_404(PortalCompany, slug=slug, is_active=True)

    if request.method == "POST":
        password = request.POST.get("password", "").strip()

        if company.check_manager_password(password):
            role = "managers"
        elif company.check_staff_password(password):
            role = "staff"
        else:
            messages.error(request, "❌ Неверный пароль.")
            return render(request, "entry_portal/company_login.html", {"company": company})

        # 🔹 очищаем прежний контекст компании/роли
        for k in ("company_slug", "company_name", "user_role"):
            request.session.pop(k, None)

        # 🔹 техпользователь для сессии
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=f"portal__{company.slug}",
            defaults={"is_active": True}
        )
        if created and hasattr(user, "set_unusable_password"):
            user.set_unusable_password()
            user.save(update_fields=["password"])

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        # 🔹 кладём свежий контекст
        request.session["company_slug"] = company.slug
        request.session["company_name"] = company.name
        request.session["user_role"] = role

        # 🔹 выбираем целевой путь:
        # 1) если в БД у компании заполнен redirect_url — идём туда
        # 2) иначе берём из мапы TARGETS
        # 3) иначе на корень
        target = company.redirect_url or TARGETS.get(company.slug, "/")

        # обязательно абсолютный путь (начинается с "/")
        if not target.startswith("/"):
            target = "/" + target

        return redirect(target)

    return render(request, "entry_portal/company_login.html", {"company": company})