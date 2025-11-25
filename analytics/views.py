from datetime import datetime
from io import StringIO
import csv

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone

from .services import (
    default_window, Window,
    shares_by_doctor, shares_by_clinic, shares_by_brand, active_campaigns_summary
)

def _parse_ymd(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None

@login_required
@user_passes_test(lambda u: u.is_staff)
def analytics_dashboard(request):
    start = _parse_ymd(request.GET.get("from") or "") or (timezone.now() - timezone.timedelta(days=30))
    end = _parse_ymd(request.GET.get("to") or "") or timezone.now()
    win = Window(start=start, end=end)

    by_doc, doc_totals = shares_by_doctor(win)
    by_clinic, clinic_totals = shares_by_clinic(win)
    by_brand, brand_totals = shares_by_brand(win)
    campaigns = active_campaigns_summary()

    ctx = {
        "start": start.date(),
        "end": end.date(),
        "by_doc": by_doc,
        "by_doc_totals": doc_totals,
        "by_clinic": by_clinic,
        "by_clinic_totals": clinic_totals,
        "by_brand": by_brand,
        "by_brand_totals": brand_totals,
        "campaigns": campaigns,
    }
    return render(request, "analytics/dashboard.html", ctx)

@login_required
@user_passes_test(lambda u: u.is_staff)
def export_csv(request, kind: str):
    start = _parse_ymd(request.GET.get("from") or "") or (timezone.now() - timezone.timedelta(days=30))
    end = _parse_ymd(request.GET.get("to") or "") or timezone.now()
    win = Window(start=start, end=end)

    if kind == "doctor":
        rows, totals = shares_by_doctor(win)
        headers = ["doctor_id", "doctor_name", "clinic_name", "shares", "clicked", "ctr"]
    elif kind == "clinic":
        rows, totals = shares_by_clinic(win)
        headers = ["clinic_id", "clinic_name", "shares", "clicked", "ctr"]
    elif kind == "brand":
        rows, totals = shares_by_brand(win)
        headers = ["brand_id", "brand_name", "shares", "clicked", "ctr"]
    else:
        return HttpResponse("Unknown export", status=400)

    sio = StringIO()
    w = csv.DictWriter(sio, fieldnames=headers)
    w.writeheader()
    for r in rows:
        r = dict(r)
        r["ctr"] = f"{r['ctr']:.2%}"
        w.writerow(r)
    # totals row
    t = {h: "" for h in headers}
    t[headers[-3]] = "TOTAL"  # place total label into first non-id column
    t["shares"] = totals["shares"]
    t["clicked"] = totals["clicked"]
    t["ctr"] = f"{totals['ctr']:.2%}"
    w.writerow(t)

    resp = HttpResponse(sio.getvalue(), content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="analytics_{kind}_{start.date()}_{end.date()}.csv"'
    return resp
