from django.contrib import admin, messages
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.utils.html import format_html

from .models import Campaign, CampaignSubtopic, DoctorCampaign
from registration.models import RegistrationLink

class CampaignSubtopicInline(admin.TabularInline):
    model = CampaignSubtopic
    extra = 1

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "therapy_area", "start_date", "end_date", "max_doctors", "is_active_flag", "doctors_count", "create_link_btn")
    list_filter = ("brand", "therapy_area", "is_active_flag")
    search_fields = ("name",)
    inlines = [CampaignSubtopicInline]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:pk>/create_link/", self.admin_site.admin_view(self.create_link_view), name="campaign-create-link"),
        ]
        return custom + urls

    def create_link_btn(self, obj):
        url = reverse("admin:campaign-create-link", args=[obj.pk])
        return format_html('<a class="button" href="{}">Create doctor registration link</a>', url)
    create_link_btn.short_description = "Registration link"

    def create_link_view(self, request, pk):
        campaign = self.get_object(request, pk)
        if not campaign:
            self.message_user(request, "Campaign not found.", level=messages.ERROR)
            return HttpResponseRedirect("../")
        # create a new campaign-bound link
        link = RegistrationLink.objects.create(
            campaign=campaign,
            is_self=False,
            label=f"{campaign.brand.name}-{campaign.name}",
            created_by=request.user if request.user.is_authenticated else None,
        )
        self.message_user(request, f"Link created: /fr/{link.token}/", level=messages.SUCCESS)
        return HttpResponseRedirect(reverse("admin:registration_registrationlink_change", args=[link.pk]))

@admin.register(DoctorCampaign)
class DoctorCampaignAdmin(admin.ModelAdmin):
    list_display = ("doctor", "campaign", "registered_via", "fieldrep", "end_date_snapshot", "created_at")
    list_filter = ("registered_via", "campaign__brand", "campaign__therapy_area")
    search_fields = ("doctor__full_name", "doctor__imc_number", "campaign__name")
