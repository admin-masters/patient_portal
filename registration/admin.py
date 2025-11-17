# registration/admin.py
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import reverse
from .models import RegistrationLink, DoctorRegistration

class RegistrationLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "is_self", "is_active", "uses_count", "share_path", "download_txt")
    readonly_fields = ("token", "uses_count", "created_at", "share_preview")
    search_fields = ("label", "token")
    list_filter = ("is_self", "is_active")

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:pk>/download/", self.admin_site.admin_view(self.download_link), name="registrationlink-download"),
        ]
        return custom + urls

    def share_path(self, obj):
        # relative path is safe to copy; absolute link comes from download endpoint
        return f"/r/{obj.token}/"
    share_path.short_description = "Shareable path"

    def share_preview(self, obj):
        return format_html("<code>/r/{}/</code>", obj.token)

    def download_txt(self, obj):
        url = reverse("admin:registrationlink-download", args=[obj.pk])
        return format_html('<a class="button" href="{}">Download link</a>', url)
    download_txt.short_description = "Download"

    def download_link(self, request, pk):
        obj = self.get_object(request, pk)
        # build absolute URL
        abs_url = request.build_absolute_uri(f"/r/{obj.token}/")
        body = f"Self-registration link:\n{abs_url}\n"
        resp = HttpResponse(body, content_type="text/plain")
        resp["Content-Disposition"] = f'attachment; filename="self_registration_{obj.pk}.txt"'
        return resp

admin.site.register(RegistrationLink, RegistrationLinkAdmin)
admin.site.register(DoctorRegistration)
