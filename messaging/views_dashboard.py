# messaging/views_dashboard.py
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.shortcuts import render
from .models import OutboundMessage

@login_required
@user_passes_test(lambda u: u.is_staff)
def messages_dashboard(request):
    qs = OutboundMessage.objects.all()
    by_status = (qs.values("channel", "status")
                   .annotate(total=Count("id"))
                   .order_by("channel", "status"))

    by_day = (qs.annotate(day=TruncDate("created_at"))
                .values("day", "channel", "status")
                .annotate(total=Count("id"))
                .order_by("day", "channel", "status"))

    return render(request, "messaging/dashboard.html", {
        "by_status": by_status,
        "by_day": by_day,
    })
