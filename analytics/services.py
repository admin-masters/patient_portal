from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Tuple, Iterable, Optional

from django.db.models import Q
from django.utils import timezone

from sharing.models import ShareEvent, ShareLink, LinkVisit
from accounts.models import Doctor
from clinics.models import Clinic
from campaigns.models import Campaign, DoctorCampaign
from brands.models import Brand

@dataclass
class Window:
    start: datetime
    end: datetime

def default_window(days: int = 30) -> Window:
    tz_now = timezone.now()
    end = tz_now
    start = tz_now - timezone.timedelta(days=days)
    return Window(start=start, end=end)

def _shares_in_window(win: Window):
    return (ShareEvent.objects
            .select_related("doctor", "clinic")
            .filter(created_at__gte=win.start, created_at__lte=win.end))

def _clicked_links_in_window(win: Window, link_ids: Iterable[int]):
    if not link_ids:
        return set()
    qs = (LinkVisit.objects
          .filter(share_link_id__in=list(link_ids),
                  created_at__gte=win.start, created_at__lte=win.end)
          .values_list("share_link_id", flat=True)
          .distinct())
    return set(qs)

def _brand_for_share_on_date(doctor_id: int, on_date: date) -> List[Brand]:
    """
    A share can be associated with zero/one/multiple active campaigns for that doctor
    at the time of share. We count it for each active campaign's brand.
    """
    qs = (DoctorCampaign.objects
          .select_related("campaign__brand")
          .filter(doctor_id=doctor_id,
                  campaign__is_active_flag=True,
                  campaign__start_date__lte=on_date,
                  campaign__end_date__gte=on_date))
    return [dc.campaign.brand for dc in qs]

def shares_by_doctor(win: Window):
    shares = list(_shares_in_window(win)
                  .values("id", "doctor_id", "doctor__full_name", "clinic_id", "clinic__name", "share_link_id", "created_at"))

    link_ids = [s["share_link_id"] for s in shares]
    clicked = _clicked_links_in_window(win, link_ids)

    agg = defaultdict(lambda: {"doctor_name": "", "clinic_name": "", "shares": 0, "clicked": 0})
    for s in shares:
        k = s["doctor_id"]
        a = agg[k]
        a["doctor_name"] = s["doctor__full_name"]
        a["clinic_name"] = s["clinic__name"]
        a["shares"] += 1
        if s["share_link_id"] in clicked:
            a["clicked"] += 1

    # compute CTR
    rows = []
    for k, v in agg.items():
        ctr = (v["clicked"] / v["shares"]) if v["shares"] else 0.0
        rows.append({
            "doctor_id": k,
            "doctor_name": v["doctor_name"],
            "clinic_name": v["clinic_name"],
            "shares": v["shares"],
            "clicked": v["clicked"],
            "ctr": ctr,
        })
    rows.sort(key=lambda x: x["shares"], reverse=True)
    totals = {
        "shares": sum(r["shares"] for r in rows),
        "clicked": sum(r["clicked"] for r in rows),
    }
    totals["ctr"] = (totals["clicked"] / totals["shares"]) if totals["shares"] else 0.0
    return rows, totals

def shares_by_clinic(win: Window):
    shares = list(_shares_in_window(win)
                  .values("id", "clinic_id", "clinic__name", "share_link_id"))

    link_ids = [s["share_link_id"] for s in shares]
    clicked = _clicked_links_in_window(win, link_ids)

    agg = defaultdict(lambda: {"clinic_name": "", "shares": 0, "clicked": 0})
    for s in shares:
        k = s["clinic_id"]
        a = agg[k]
        a["clinic_name"] = s["clinic__name"]
        a["shares"] += 1
        if s["share_link_id"] in clicked:
            a["clicked"] += 1

    rows = []
    for k, v in agg.items():
        ctr = (v["clicked"] / v["shares"]) if v["shares"] else 0.0
        rows.append({
            "clinic_id": k,
            "clinic_name": v["clinic_name"],
            "shares": v["shares"],
            "clicked": v["clicked"],
            "ctr": ctr,
        })
    rows.sort(key=lambda x: x["shares"], reverse=True)
    totals = {
        "shares": sum(r["shares"] for r in rows),
        "clicked": sum(r["clicked"] for r in rows),
    }
    totals["ctr"] = (totals["clicked"] / totals["shares"]) if totals["shares"] else 0.0
    return rows, totals

def shares_by_brand(win: Window):
    # We project each share to zero/one/many brands based on active tags at share time
    se = list(_shares_in_window(win)
              .values("id", "doctor_id", "share_link_id", "created_at"))

    link_ids = [s["share_link_id"] for s in se]
    clicked = _clicked_links_in_window(win, link_ids)

    agg = defaultdict(lambda: {"shares": 0, "clicked": 0})
    brand_names = {}  # brand_id -> name

    for s in se:
        b_list = _brand_for_share_on_date(s["doctor_id"], s["created_at"].date())
        # If no active brand/campaign, we skip; or you may choose to count under "Unattributed"
        for b in b_list:
            brand_names[b.id] = b.name
            a = agg[b.id]
            a["shares"] += 1
            if s["share_link_id"] in clicked:
                a["clicked"] += 1

    rows = []
    for bid, v in agg.items():
        ctr = (v["clicked"] / v["shares"]) if v["shares"] else 0.0
        rows.append({
            "brand_id": bid,
            "brand_name": brand_names.get(bid, f"Brand {bid}"),
            "shares": v["shares"],
            "clicked": v["clicked"],
            "ctr": ctr,
        })
    rows.sort(key=lambda x: x["shares"], reverse=True)
    totals = {
        "shares": sum(r["shares"] for r in rows),
        "clicked": sum(r["clicked"] for r in rows),
    }
    totals["ctr"] = (totals["clicked"] / totals["shares"]) if totals["shares"] else 0.0
    return rows, totals

def active_campaigns_summary():
    today = timezone.localdate()
    qs = (Campaign.objects
          .select_related("brand", "therapy_area")
          .filter(is_active_flag=True, start_date__lte=today, end_date__gte=today))
    rows = []
    for c in qs:
        rows.append({
            "brand": c.brand.name,
            "campaign": c.name,
            "therapy_area": c.therapy_area.name,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "max_doctors": c.max_doctors or None,
            "doctors_tagged": c.doctor_tags.count(),
            "capacity_left": (None if not c.max_doctors else max(c.max_doctors - c.doctor_tags.count(), 0)),
        })
    rows.sort(key=lambda r: (r["brand"], r["campaign"]))
    return rows
