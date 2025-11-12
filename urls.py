from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # ← добавили
from django.views.generic import RedirectView
from django.urls import re_path


urlpatterns = [

    re_path(
        r"^contact/(?P<id>\d+)/view/?$",
        RedirectView.as_view(pattern_name="view_contact", permanent=False),
    ),
    path("admin/", admin.site.urls),

    # Экран выбора компании + логин по паролю компании
    path("", include("entry_portal.urls")),      # /  → choose_company, /login/<slug>/ → portal_login

    # Твои модули
    path("crm/", include("crm.urls")),
    path("scales/", include("scales.urls")),
]

# ⚙️ Раздача медиафайлов при DEBUG=True (логотипы, PDF и т.п.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
