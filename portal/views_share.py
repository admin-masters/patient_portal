# portal/views_share.py
from django.views.generic import TemplateView, FormView
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings
from django.db import connection
from django.db.models.expressions import RawSQL
from clinics.models import Clinic
from content.models import Video, Subtopic, VideoI18n
from core.models import Language
from sharing.services import create_share
from .forms import ShareForm
from .views import ClinicContextMixin   # from Sprint 4 mixin

def _abs(request, path: str) -> str:
    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    return f"{scheme}://{host}{path}"

class ShareComposeView(ClinicContextMixin, FormView):
    template_name = "portal/share.html"
    form_class = ShareForm

    def dispatch(self, request, *args, **kwargs):
        self.clinic = get_object_or_404(Clinic, portal_slug=kwargs.get("slug"))
        if not self.user_is_member():
            return HttpResponseForbidden("You do not have access to this clinic's portal.")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        init = super().get_initial()
        init["language"] = self.clinic.default_language_id
        return init

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clinic"] = self.clinic
        return ctx

    # inside ShareComposeView.form_valid (replace the body)
    def form_valid(self, form):
        kind = "portal" if "__portal__" in self.request.POST else form.cleaned_data["share_kind"]
        lang = form.cleaned_data["language"].code
        msisdn = form.cleaned_data["patient_msisdn"]
        video = form.cleaned_data.get("video")
        subtopic = form.cleaned_data.get("subtopic")

        link, event, om, deeplink = create_share(
            clinic=self.clinic, language_code=lang, patient_msisdn=msisdn,
            share_type=kind if kind in ("video", "subtopic", "portal") else "video",
            video=video, subtopic=subtopic, acting_user=self.request.user
        )
        om.body_rendered = om.body_rendered.replace("/s/", _abs(self.request, "/s/"))
        om.save(update_fields=["body_rendered"])

        self.success_url = reverse("portal:share_confirm",
                                   kwargs={"slug": self.clinic.portal_slug, "token": link.token})
        self.request.session[f"wa:{link.token}"] = deeplink
        return super().form_valid(form)


# Confirmation page: show message + "Open WhatsApp" button
class ShareConfirmView(ClinicContextMixin, TemplateView):
    template_name = "portal/share_confirm.html"

    def dispatch(self, request, *args, **kwargs):
        self.clinic = get_object_or_404(Clinic, portal_slug=kwargs.get("slug"))
        if not self.user_is_member():
            return HttpResponseForbidden("You do not have access to this clinic's portal.")
        self.token = kwargs.get("token")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from sharing.models import ShareLink
        from messaging.models import OutboundMessage

        ctx = super().get_context_data(**kwargs)
        link = get_object_or_404(ShareLink, token=self.token, clinic=self.clinic)
        om = OutboundMessage.objects.filter(share_event__share_link=link).order_by("-created_at").first()
        wa = self.request.session.pop(f"wa:{link.token}", None)
        ctx.update({
            "clinic": self.clinic,
            "share_link": _abs(self.request, f"/s/{link.token}/"),
            "message_preview": om.body_rendered if om else "",
            "wa_deeplink": wa,
        })
        return ctx

# ---------- AJAX endpoints ----------
# 1) videos by subtopic (for dropdown fill)
def ajax_videos_for_subtopic(request, slug):
    if request.method != "GET":
        raise Http404
    clinic = get_object_or_404(Clinic, portal_slug=slug)
    subtopic_id = request.GET.get("subtopic")
    if not subtopic_id:
        return JsonResponse({"items": []})
    vids = (Video.objects.filter(subtopic_id=subtopic_id, is_active=True)
            .order_by("sort_order", "title_en")
            .values("id", "title_en"))
    return JsonResponse({"items": list(vids)})

# 2) languages available for a selected video
def ajax_languages_for_video(request, slug):
    if request.method != "GET":
        raise Http404
    video_id = request.GET.get("video")
    if not video_id:
        return JsonResponse({"langs": []})
    langs = list(VideoI18n.objects.filter(video_id=video_id, is_published=True)
                 .values_list("language_id", flat=True))
    return JsonResponse({"langs": langs})

# 3) typeahead: search by title/keywords (localized + english)
def ajax_suggest_titles(request, slug):
    if request.method != "GET":
        raise Http404
    q = (request.GET.get("q") or "").strip()
    lang = request.GET.get("lang") or None
    if not q:
        return JsonResponse({"items": []})
    localized = list(VideoI18n.objects.filter(is_published=True, language_id=lang)
                     .filter(title_local__search=q)[:10]
                     .values_list("title_local", flat=True)) if lang else []
    english = list(Video.objects.filter(is_active=True)
                   .filter(title_en__search=q)[:10]
                   .values_list("title_en", flat=True))
    # Merge unique, localized first
    seen, items = set(), []
    for t in localized + english:
        if t not in seen:
            items.append(t)
            seen.add(t)
    return JsonResponse({"items": items[:10]})


def ajax_suggest_titles(request, slug):
    if request.method != "GET":
        raise Http404
    q = (request.GET.get("q") or "").strip()
    lang = request.GET.get("lang") or None
    if not q:
        return JsonResponse({"items": []})

    if connection.vendor == "mysql":
        localized = (list(
            VideoI18n.objects.filter(is_published=True, language_id=lang)
            .annotate(score=RawSQL(
                "MATCH(title_local, keywords_local) AGAINST (%s IN NATURAL LANGUAGE MODE)", (q,)
            ))
            .filter(score__gt=0)
            .order_by("-score")
            .values_list("title_local", flat=True)[:10]
        ) if lang else [])
        english = list(
            Video.objects.filter(is_active=True)
            .annotate(score=RawSQL(
                "MATCH(title_en, keywords_en) AGAINST (%s IN NATURAL LANGUAGE MODE)", (q,)
            ))
            .filter(score__gt=0)
            .order_by("-score")
            .values_list("title_en", flat=True)[:10]
        )
    else:
        # Fallback (e.g., if someone runs SQLite locally)
        localized = (list(
            VideoI18n.objects.filter(is_published=True, language_id=lang, title_local__icontains=q)
            .values_list("title_local", flat=True)[:10]
        ) if lang else [])
        english = list(
            Video.objects.filter(is_active=True, title_en__icontains=q)
            .values_list("title_en", flat=True)[:10]
        )

    # Merge unique, localized first
    seen, items = set(), []
    for t in localized + english:
        if t not in seen:
            items.append(t)
            seen.add(t)
    return JsonResponse({"items": items[:10]})
