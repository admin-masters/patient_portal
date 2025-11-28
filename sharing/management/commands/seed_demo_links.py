from django.core.management.base import BaseCommand
from django.utils import timezone
from random import choice
from sharing.models import ShareLink
from clinics.models import Clinic
from accounts.models import Doctor
from content.models import Video, Subtopic
from core.models import Language

class Command(BaseCommand):
    help = "Create demo ShareLinks for load testing (videos/subtopics/portal)."

    def add_arguments(self, parser):
        parser.add_argument("--n", type=int, default=50)

    def handle(self, *args, **opts):
        langs = list(Language.objects.filter(is_active=True).values_list("code", flat=True)) or ["en"]
        clinic = Clinic.objects.order_by("?").first()
        doctor = Doctor.objects.order_by("?").first()
        videos = list(Video.objects.filter(is_active=True))
        subs = list(Subtopic.objects.filter(is_active=True))

        if not all([clinic, doctor, videos, subs]):
            self.stdout.write(self.style.ERROR("Need at least one clinic, doctor, subtopic and video."))
            return

        for _ in range(opts["n"]):
            kind = choice(["video", "subtopic", "portal"])
            lang = choice(langs)
            if kind == "video":
                v = choice(videos)
                ShareLink.objects.create(type="video", doctor=doctor, clinic=clinic, language_id=lang, video=v)
            elif kind == "subtopic":
                s = choice(subs)
                ShareLink.objects.create(type="subtopic", doctor=doctor, clinic=clinic, language_id=lang, subtopic=s)
            else:
                ShareLink.objects.create(type="portal", doctor=doctor, clinic=clinic, language_id=lang)
        self.stdout.write(self.style.SUCCESS("Demo ShareLinks created."))
