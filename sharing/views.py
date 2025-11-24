# sharing/views.py
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Prefetch
from django.urls import reverse
from typing import Optional

from .models import ShareLink, LinkVisit
from clinics.models import Clinic
from content.models import Subtopic, SubtopicI18n, Video, VideoI18n
from .utils import (
    youtube_id, title_for_video, name_for_subtopic,
    thumb_for_video, thumb_for_subtopic, ui_label
)

# --- helper: log a LinkVisit if token is provided & valid ---
def _log_visit(request, token: Optional[str], extra_referer: Optional[str] = None, link: Optional[ShareLink] = None):
    if not token and not link:
        return
    if not link:
        try:
            link = ShareLink.objects.get(token=token)
        except ShareLink.DoesNotExist:
            return
    LinkVisit.objects.create(
        share_link=link,
        ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        referer=extra_referer or request.META.get("HTTP_REFERER", ""),
    )

class ShareLinkView(TemplateView):
    """
    Token entry point: renders appropriate patient page (video | subtopic | portal).
    """
    template_name = "sharing/patient_home.html"  # replaced at runtime

    def dispatch(self, request, *args, **kwargs):
        self.link: ShareLink = get_object_or_404(ShareLink, token=kwargs.get("token"))
        # First impression tracking
        _log_visit(request, token=None, link=self.link, extra_referer="token:landing")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.link.type == "video":
            return ["sharing/patient_video.html"]
        if self.link.type == "subtopic":
            return ["sharing/patient_subtopic.html"]
        return ["sharing/patient_home.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lang = self.link.language_id
        clinic = self.link.clinic

        if self.link.type == "video":
            video = self.link.video
            vloc = VideoI18n.objects.filter(video=video, language_id=lang).first() or \
                   VideoI18n.objects.filter(video=video, language_id="en").first()
            vid_url = vloc.youtube_url if vloc else None
            vid_id = youtube_id(vid_url) if vid_url else None

            ctx.update({
                "page_type": "video",
                "clinic": clinic,
                "lang": lang,
                "labels": {
                    "for_more_videos": ui_label("for_more_videos", lang),
                    "back_to_home": ui_label("back_to_home", lang),
                },
                "video": video,
                "video_title": title_for_video(video, lang),
                "video_thumb": thumb_for_video(video, lang),
                "youtube_id": vid_id,
                "subtopic": video.subtopic,
                "subtopic_name": name_for_subtopic(video.subtopic, lang),
                # "For more videos" → subtopic page; include ?t=<token> so we can keep tracking
                "more_url": reverse("sharing:patient_subtopic",
                                    kwargs={"slug": clinic.portal_slug, "lang": lang, "sub_slug": video.subtopic.slug})
                           + f"?t={self.link.token}",
                "home_url": reverse("sharing:patient_home",
                                    kwargs={"slug": clinic.portal_slug, "lang": lang}) + f"?t={self.link.token}",
            })
            return ctx

        if self.link.type == "subtopic":
            st = self.link.subtopic
            videos = (Video.objects
                      .filter(subtopic=st, is_active=True)
                      .order_by("sort_order", "title_en")
                      .select_related("subtopic", "subtopic__therapy_area"))
            listing = []
            for v in videos:
                listing.append({
                    "title": title_for_video(v, lang),
                    "thumb": thumb_for_video(v, lang),
                    "url": reverse("sharing:patient_video",
                                   kwargs={"slug": clinic.portal_slug, "lang": lang, "vid_slug": v.slug})
                           + f"?t={self.link.token}",
                })
            ctx.update({
                "page_type": "subtopic",
                "clinic": clinic,
                "lang": lang,
                "labels": {
                    "for_more_videos": ui_label("for_more_videos", lang),
                    "subtopics": ui_label("subtopics", lang),
                    "back_to_home": ui_label("back_to_home", lang),
                },
                "subtopic": st,
                "subtopic_name": name_for_subtopic(st, lang),
                "subtopic_thumb": thumb_for_subtopic(st, lang),
                "videos": listing,
                "home_url": reverse("sharing:patient_home",
                                    kwargs={"slug": clinic.portal_slug, "lang": lang}) + f"?t={self.link.token}",
            })
            return ctx

        # portal (home)
        subs = (Subtopic.objects
                .filter(is_active=True)
                .order_by("sort_order", "slug")
                .select_related("therapy_area"))
        listing = []
        for s in subs:
            listing.append({
                "name": name_for_subtopic(s, lang),
                "thumb": thumb_for_subtopic(s, lang),
                "url": reverse("sharing:patient_subtopic",
                               kwargs={"slug": clinic.portal_slug, "lang": lang, "sub_slug": s.slug})
                       + f"?t={self.link.token}",
            })
        ctx.update({
            "page_type": "home",
            "clinic": clinic,
            "lang": lang,
            "labels": {"subtopics": ui_label("subtopics", lang)},
            "subtopics": listing,
        })
        return ctx

# ---- Non-token browsing pages (keep token in ?t= for continued tracking) ----

class PatientHomeView(TemplateView):
    template_name = "sharing/patient_home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = kwargs["slug"]
        lang = kwargs["lang"]
        clinic = get_object_or_404(Clinic, portal_slug=slug)
        token = self.request.GET.get("t")
        if token:
            _log_visit(self.request, token, extra_referer="internal:home")

        subs = (Subtopic.objects
                .filter(is_active=True)
                .order_by("sort_order", "slug")
                .select_related("therapy_area"))
        listing = []
        for s in subs:
            url = reverse("sharing:patient_subtopic",
                          kwargs={"slug": slug, "lang": lang, "sub_slug": s.slug})
            if token:
                url += f"?t={token}"
            listing.append({"name": name_for_subtopic(s, lang), "thumb": thumb_for_subtopic(s, lang), "url": url})

        ctx.update({
            "page_type": "home",
            "clinic": clinic,
            "lang": lang,
            "labels": {"subtopics": ui_label("subtopics", lang)},
            "subtopics": listing,
        })
        return ctx

class PatientSubtopicView(TemplateView):
    template_name = "sharing/patient_subtopic.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = kwargs["slug"]; lang = kwargs["lang"]; sub_slug = kwargs["sub_slug"]
        clinic = get_object_or_404(Clinic, portal_slug=slug)
        subtopic = get_object_or_404(Subtopic, slug=sub_slug)
        token = self.request.GET.get("t")
        if token:
            _log_visit(self.request, token, extra_referer=f"internal:subtopic:{sub_slug}")

        videos = (Video.objects.filter(subtopic=subtopic, is_active=True)
                  .order_by("sort_order", "title_en"))
        listing = []
        for v in videos:
            url = reverse("sharing:patient_video",
                          kwargs={"slug": slug, "lang": lang, "vid_slug": v.slug})
            if token:
                url += f"?t={token}"
            listing.append({"title": title_for_video(v, lang), "thumb": thumb_for_video(v, lang), "url": url})

        home_url = reverse("sharing:patient_home", kwargs={"slug": slug, "lang": lang})
        if token: home_url += f"?t={token}"

        ctx.update({
            "page_type": "subtopic",
            "clinic": clinic,
            "lang": lang,
            "labels": {
                "for_more_videos": ui_label("for_more_videos", lang),
                "subtopics": ui_label("subtopics", lang),
                "back_to_home": ui_label("back_to_home", lang),
            },
            "subtopic": subtopic,
            "subtopic_name": name_for_subtopic(subtopic, lang),
            "subtopic_thumb": thumb_for_subtopic(subtopic, lang),
            "videos": listing,
            "home_url": home_url,
        })
        return ctx

class PatientVideoView(TemplateView):
    template_name = "sharing/patient_video.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = kwargs["slug"]; lang = kwargs["lang"]; vid_slug = kwargs["vid_slug"]
        clinic = get_object_or_404(Clinic, portal_slug=slug)
        video = get_object_or_404(Video, slug=vid_slug)
        token = self.request.GET.get("t")
        if token:
            _log_visit(self.request, token, extra_referer=f"internal:video:{vid_slug}")

        vloc = VideoI18n.objects.filter(video=video, language_id=lang).first() or \
               VideoI18n.objects.filter(video=video, language_id="en").first()
        vid_url = vloc.youtube_url if vloc else None
        vid_id = youtube_id(vid_url) if vid_url else None

        more_url = reverse("sharing:patient_subtopic",
                           kwargs={"slug": slug, "lang": lang, "sub_slug": video.subtopic.slug})
        home_url = reverse("sharing:patient_home", kwargs={"slug": slug, "lang": lang})
        if token:
            more_url += f"?t={token}"
            home_url += f"?t={token}"

        ctx.update({
            "page_type": "video",
            "clinic": clinic,
            "lang": lang,
            "labels": {
                "for_more_videos": ui_label("for_more_videos", lang),
                "back_to_home": ui_label("back_to_home", lang),
            },
            "video": video,
            "video_title": title_for_video(video, lang),
            "video_thumb": thumb_for_video(video, lang),
            "youtube_id": vid_id,
            "subtopic": video.subtopic,
            "subtopic_name": name_for_subtopic(video.subtopic, lang),
            "more_url": more_url,
            "home_url": home_url,
        })
        return ctx
