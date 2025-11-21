# sharing/services.py
from urllib.parse import quote_plus
from typing import Optional, Tuple
from django.db import transaction
from django.shortcuts import get_object_or_404

from accounts.models import Doctor
from clinics.models import Clinic, DoctorClinic
from content.models import Video, Subtopic, VideoI18n, SubtopicI18n
from core.models import Language
from .models import ShareLink, ShareEvent
from messaging.models import OutboundMessage
from messaging.services import render_message

def _pick_doctor_for_clinic(clinic: Clinic, acting_user=None) -> Doctor:
    """
    Prefer the Doctor explicitly linked to the acting user (if your portal membership stores it),
    otherwise use the clinic's primary doctor.
    """
    # If acting_user has ClinicMember.doctor set, use that (Sprint 4 stored optional link)
    if hasattr(acting_user, "clinic_memberships"):
        cm = acting_user.clinic_memberships.filter(clinic=clinic, is_active=True, doctor__isnull=False).first()
        if cm and cm.doctor:
            return cm.doctor

    dc = DoctorClinic.objects.filter(clinic=clinic, is_primary=True).select_related("doctor").first()
    if dc:
        return dc.doctor
    # fallback: any doctor linked
    any_dc = DoctorClinic.objects.filter(clinic=clinic).select_related("doctor").first()
    if any_dc:
        return any_dc.doctor
    raise ValueError("No doctor found for clinic")

def _video_title_in_language(video: Video, language_code: str) -> str:
    vloc = VideoI18n.objects.filter(video=video, language_id=language_code).first()
    return vloc.title_local if vloc else video.title_en

def _subtopic_name_in_language(subtopic: Subtopic, language_code: str) -> str:
    sloc = SubtopicI18n.objects.filter(subtopic=subtopic, language_id=language_code).first()
    return sloc.name_local if sloc else subtopic.slug

def build_whatsapp_deeplink(msisdn_10: str, message: str) -> str:
    # Indian numbers: prefix +91
    return f"https://wa.me/91{msisdn_10}?text={quote_plus(message)}"

@transaction.atomic
def create_share(
    *, clinic: Clinic, language_code: str, patient_msisdn: str,
    share_type: str, video: Optional[Video] = None, subtopic: Optional[Subtopic] = None,
    acting_user=None
) -> Tuple[ShareLink, ShareEvent, OutboundMessage, str]:
    """
    Create ShareLink + ShareEvent + OutboundMessage and return wa.me deep-link.
    """
    # Resolve doctor (display name in message)
    doctor = _pick_doctor_for_clinic(clinic, acting_user=acting_user)
    Language.objects.get(code=language_code)  # ensure exists

    # Build share link first (used in message)
    link = ShareLink.objects.create(
        type=share_type, doctor=doctor, clinic=clinic, language_id=language_code,
        video=video if share_type == "video" else None,
        subtopic=subtopic if share_type == "subtopic" else None
    )
    link_url = f"/s/{link.token}/"  # local placeholder; becomes absolute in view

    # Render message by template key
    if share_type == "video":
        template_key = "share_video"
        title = _video_title_in_language(video, language_code)
        ctx = {"doctor_name": f"Dr. {doctor.full_name}", "title": title, "link": link_url}
    elif share_type == "subtopic":
        template_key = "share_subtopic"
        name = _subtopic_name_in_language(subtopic, language_code)
        ctx = {"doctor_name": f"Dr. {doctor.full_name}", "subtopic": name, "link": link_url}
    else:
        template_key = "share_portal"
        ctx = {"doctor_name": f"Dr. {doctor.full_name}", "link": link_url}

    body = render_message(template_key, language_code, channel="whatsapp", context=ctx)

    # Persist share event + outbound record
    event = ShareEvent.objects.create(
        type=share_type, doctor=doctor, clinic=clinic, language_id=language_code,
        video=video if share_type == "video" else None,
        subtopic=subtopic if share_type == "subtopic" else None,
        patient_msisdn=patient_msisdn,
        share_link=link,
        channel="whatsapp",
        message_preview=body,
    )
    om = OutboundMessage.objects.create(
        share_event=event, to_msisdn=patient_msisdn, channel="whatsapp",
        language_id=language_code, template_key=template_key, body_rendered=body, status="queued"
    )

    # Build WhatsApp deep-link
    deeplink = build_whatsapp_deeplink(patient_msisdn, body)
    return link, event, om, deeplink
