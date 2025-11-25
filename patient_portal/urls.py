# pedi_portal/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from messaging.views_dashboard import messages_dashboard
from messaging.views_webhooks import waba_webhook, sendgrid_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("registration.urls")),
    path("", include("portal.urls")),
    path("", include("sharing.urls")),    # ← add
    path("", include("analytics.urls")),   # ← add

    path("hooks/waba/", waba_webhook, name="waba_webhook"),
    path("hooks/sendgrid/", sendgrid_webhook, name="sendgrid_webhook"),

    path("ops/messages/", messages_dashboard, name="messages_dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
