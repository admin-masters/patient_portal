# portal/services.py
from django.db.models import Q
from django.utils import timezone
from typing import List, Dict

from clinics.models import Clinic
from accounts.models import Doctor
from campaigns.models import DoctorCampaign, Campaign, CampaignSubtopic
from core.models import Language
from content.models import Video, VideoI18n, SubtopicI18n

def search_catalog(query: str, lang_code: str | None, limit: int = 50):
    """
    Returns (localized_hits, english_hits) lists.
    localized_hits are VideoI18n; english_hits are Video.
    """
    localized = []
    if lang_code:
        localized = (VideoI18n.objects
                     .select_related("video", "video__subtopic", "video__subtopic__therapy_area")
                     .filter(language__code=lang_code, is_published=True)
                     .filter(Q(title_local__search=query) | Q(keywords_local__search=query))
                     [:limit])
    english = (Video.objects
               .select_related("subtopic", "subtopic__therapy_area")
               .filter(is_active=True)
               .filter(Q(title_en__search=query) | Q(keywords_en__search=query))
               [:limit])
    return list(localized), list(english)

def language_choices() -> List[str]:
    return list(Language.objects.filter(is_active=True).values_list("code", flat=True))

def active_campaign_banners_for_clinic(clinic: Clinic, lang_code: str | None = None) -> List[Dict]:
    """
    Compute banners for the clinic across all its doctors' active campaigns.
    One banner per campaign.
    Returns list of dicts with: text, brand, campaign, therapy_area, subtopics_txt
    Ordered by (end_date ASC, brand.name ASC).
    """
    today = timezone.localdate()
    # All doctors linked to the clinic (through DoctorClinic)
    doctor_ids = list(Doctor.objects.filter(doctorclinic__clinic=clinic).values_list("id", flat=True))
    if not doctor_ids:
        return []

    qs = (DoctorCampaign.objects
          .select_related("campaign__brand", "campaign__therapy_area")
          .filter(doctor_id__in=doctor_ids,
                  campaign__is_active_flag=True,
                  campaign__start_date__lte=today,
                  campaign__end_date__gte=today))

    # Build a unique set of campaigns
    campaign_ids = {dc.campaign_id for dc in qs}
    if not campaign_ids:
        return []

    campaigns = (Campaign.objects
                 .select_related("brand", "therapy_area")
                 .filter(id__in=campaign_ids)
                 .order_by("end_date", "brand__name"))

    result = []
    for camp in campaigns:
        # Resolve subtopic names (localized if possible)
        subtopics = (CampaignSubtopic.objects
                     .filter(campaign=camp)
                     .select_related("subtopic"))
        subtopics_txt = ""
        if subtopics.exists():
            if lang_code:
                # try localized names
                names = (SubtopicI18n.objects
                         .filter(subtopic__in=[s.subtopic for s in subtopics], language__code=lang_code)
                         .values_list("name_local", flat=True))
                loc_map = {si.subtopic_id: si.name_local for si in SubtopicI18n.objects.filter(
                    subtopic__in=[s.subtopic for s in subtopics], language__code=lang_code)}
                names = []
                for s in subtopics:
                    n = loc_map.get(s.subtopic_id) or s.subtopic.slug
                    names.append(n)
                subtopics_txt = ", ".join(names[:5])  # avoid very long lists
            else:
                subtopics_txt = ", ".join(s.subtopic.slug for s in subtopics[:5])

        area = camp.therapy_area.name
        brand = camp.brand.name

        if subtopics_txt:
            text = f"The {area} videos (subtopics: {subtopics_txt}) in this system are supported by {brand} for your clinic."
        else:
            text = f"The {area} videos in this system are supported by {brand} for your clinic."

        result.append({
            "text": text,
            "brand": brand,
            "campaign": camp.name,
            "therapy_area": area,
            "subtopics_txt": subtopics_txt,
            "start_date": camp.start_date,
            "end_date": camp.end_date,
        })
    return result
