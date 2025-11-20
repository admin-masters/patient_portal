# portal/admin.py
from django.contrib import admin
from .models import ClinicMember

@admin.register(ClinicMember)
class ClinicMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "clinic", "role", "doctor", "is_active", "created_at")
    list_filter  = ("role", "is_active", "clinic__state")
    search_fields = ("user__email", "user__username", "clinic__name", "doctor__imc_number")
