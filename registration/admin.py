from django.contrib import admin
from django.urls import path, reverse
from django.http import HttpResponse
from django.utils.html import format_html

from .models import RegistrationLink, DoctorRegistration

@admin.register(RegistrationLink)
class RegistrationLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "campaign", "is_self", "is_active", "uses_count", "share_path", "download_txt")
    readonly_fields = ("token", "uses_count", "created_at", "share_preview")
    search_fields = ("label", "token")
    list_filter = ("is_self", "is_active", "campaign__brand")

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:pk>/download/", self.admin_site.admin_view(self.download_link), name="registrationlink-download"),
        ]
        return custom + urls

    def share_path(self, obj):
        path = f"/r/{obj.token}/" if obj.is_self or not obj.campaign_id else f"/fr/{obj.token}/"
        return path
    share_path.short_description = "Shareable path"

    def share_preview(self, obj):
        p = self.share_path(obj)
        return format_html("<code>{}</code>", p)

    def download_txt(self, obj):
        url = reverse("admin:registrationlink-download", args=[obj.pk])
        return format_html('<a class="button" href="{}">Download link</a>', url)
    download_txt.short_description = "Download"

    def download_link(self, request, pk):
        obj = self.get_object(request, pk)
        abs_url = request.build_absolute_uri(self.share_path(obj))
        body = f"Doctor registration link:\\n{abs_url}\\n"
        resp = HttpResponse(body, content_type="text/plain")
        resp["Content-Disposition"] = f'attachment; filename="doctor_registration_{obj.pk}.txt"'
        return resp

@admin.register(DoctorRegistration)
class DoctorRegistrationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "registered_via", "doctor", "clinic", "campaign", "fieldrep", "result")
    list_filter = ("registered_via", "result", "campaign__brand")
    search_fields = ("doctor__full_name", "doctor__imc_number", "campaign__name", "fieldrep__phone_number")
