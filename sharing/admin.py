# sharing/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist

from .models import ShareEvent

# Base URL used to build the public share link shown in Admin
PORTAL_BASE_URL = (
    getattr(settings, "PORTAL_BASE_URL", None)
    or getattr(settings, "SITE_URL", None)
    or "http://127.0.0.1:8000"
).rstrip("/")

# Common attribute names used across projects
_TOKEN_ATTRS = ("token", "share_token", "short_code", "code", "key", "slug")
_RELATED_ATTRS = (
    "link",
    "share_link",
    "portal_share",
    "magiclink",
    "share",
    "portalshare",
    "portal_link",
)

def _extract_token_from_obj(obj):
    """
    Tries to read a token from the object itself, falling back to a set of
    common related attributes (one hop) such as `obj.link` or `obj.portal_share`.
    """
    if obj is None:
        return None

    # Direct token-like fields
    for attr in _TOKEN_ATTRS:
        try:
            val = getattr(obj, attr, None)
        except Exception:
            val = None
        if val:
            return val

    # One-hop related object scan for a token-like field
    for rel_name in _RELATED_ATTRS:
        try:
            rel_obj = getattr(obj, rel_name, None)
        except Exception:
            rel_obj = None
        if rel_obj:
            tok = _extract_token_from_obj(rel_obj)
            if tok:
                return tok

    return None


# Build raw_id_fields dynamically (only for fields that actually exist)
RAW_ID_FIELDS = []
for field_name in ("patient", "content", "created_by", "updated_by", "actor"):
    try:
        ShareEvent._meta.get_field(field_name)
        RAW_ID_FIELDS.append(field_name)
    except FieldDoesNotExist:
        pass


@admin.register(ShareEvent)
class ShareEventAdmin(admin.ModelAdmin):
    """
    Admin for ShareEvent that prominently exposes the token and public Share URL.
    This version is defensive: it uses callables for list_display so it won't
    explode if your model lacks fields like 'channel' or 'status'.
    """
    save_on_top = True
    list_per_page = 50
    ordering = ("-id",)

    # All columns are callables to avoid import-time field resolution errors.
    list_display = (
        "id",
        "display_patient",
        "display_channel",
        "display_status",
        "display_created",
        "display_token",
        "share_url",
    )

    # Read-only computed fields visible on the object detail page
    readonly_fields = ("display_token", "share_url")

    # Keep search simple and safe; you can expand as needed
    search_fields = ("id",)

    # Use FK pickers where available (computed above)
    raw_id_fields = tuple(RAW_ID_FIELDS)

    # -------- Display helpers (safe even if fields are missing) -------- #

    def display_patient(self, obj):
        p = getattr(obj, "patient", None)
        if not p:
            return "-"
        # Prefer full_name/name; gracefully fall back
        name = (
            getattr(p, "full_name", None)
            or getattr(p, "name", None)
            or " ".join(
                [x for x in [getattr(p, "first_name", None), getattr(p, "last_name", None)] if x]
            ).strip()
        )
        phone = (
            getattr(p, "msisdn", None)
            or getattr(p, "phone", None)
            or getattr(p, "mobile", None)
        )
        if name and phone:
            return f"{name} ({phone})"
        return name or phone or str(p)
    display_patient.short_description = "Patient"

    def display_channel(self, obj):
        return getattr(obj, "channel", "-")
    display_channel.short_description = "Channel"

    def display_status(self, obj):
        return getattr(obj, "status", "-")
    display_status.short_description = "Status"

    def display_created(self, obj):
        dt = (
            getattr(obj, "created_at", None)
            or getattr(obj, "created", None)
            or getattr(obj, "created_on", None)
            or getattr(obj, "timestamp", None)
        )
        if not dt:
            return "-"
        try:
            dt = timezone.localtime(dt)
        except Exception:
            pass
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    display_created.short_description = "Created"

    def display_token(self, obj):
        tok = _extract_token_from_obj(obj)
        return tok or "-"
    display_token.short_description = "Token"

    def share_url(self, obj):
        tok = _extract_token_from_obj(obj)
        if not tok:
            return "-"
        url = f"{PORTAL_BASE_URL}/s/{tok}/"
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    share_url.short_description = "Share URL"

    # -------- Queryset & filters (dynamic, safe) -------- #

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Select-related 'patient' if present to speed up list pages
        try:
            field = ShareEvent._meta.get_field("patient")
            if getattr(field, "many_to_one", False):
                qs = qs.select_related("patient")
        except FieldDoesNotExist:
            pass
        return qs

    def get_list_filter(self, request):
        """
        Only add list filters for fields that actually exist on the model.
        """
        filters = []
        for name in ("channel", "status"):
            try:
                ShareEvent._meta.get_field(name)
                filters.append(name)
            except FieldDoesNotExist:
                pass
        return filters
