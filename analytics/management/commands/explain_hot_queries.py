from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from analytics.services import default_window
from sharing.models import LinkVisit, ShareEvent
from content.models import Video, VideoI18n

class Command(BaseCommand):
    help = "Print EXPLAIN for a few hot queries (sanity check indexes)."

    def handle(self, *args, **kwargs):
        win = default_window(30)
        qs1 = ShareEvent.objects.filter(created_at__gte=win.start, created_at__lte=win.end).order_by("-created_at")
        qs2 = LinkVisit.objects.filter(created_at__gte=win.start, created_at__lte=win.end).order_by("-created_at")
        qs3 = Video.objects.filter(title_en__search="asthma")
        qs4 = VideoI18n.objects.filter(title_local__search="अस्थमा", language_id="hi")

        for i, qs in enumerate([qs1, qs2, qs3, qs4], start=1):
            plan = qs.explain(format="TREE")
            self.stdout.write(self.style.NOTICE(f"\n--- Query {i} ---"))
            self.stdout.write(plan)
