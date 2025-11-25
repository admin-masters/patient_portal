from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from sharing.models import ShareEvent
from messaging.models import OutboundMessage

def _is_masked(s: str | None) -> bool:
    if not s: return True
    return ("x" in s.lower()) or (len(s) != 10) or not s.isdigit()

def _mask(s: str) -> str:
    # assume 10 digits
    if not s or len(s) != 10 or not s.isdigit():
        return s
    return "x"*6 + s[-4:]

class Command(BaseCommand):
    help = "Mask patient phone numbers older than DATA_RETENTION_DAYS (default 90). Use --dry-run to preview."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=None, help="Override retention days")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        days = opts["days"] if opts["days"] is not None else getattr(settings, "DATA_RETENTION_DAYS", 90)
        cutoff = timezone.now() - timezone.timedelta(days=days)

        se_qs = ShareEvent.objects.filter(created_at__lt=cutoff)
        om_qs = OutboundMessage.objects.filter(created_at__lt=cutoff)

        se_to_mask = se_qs.exclude(patient_msisdn__isnull=True).exclude(patient_msisdn="").values_list("id", "patient_msisdn")
        om_to_mask = om_qs.exclude(to_msisdn__isnull=True).exclude(to_msisdn="").values_list("id", "to_msisdn")

        se_ids = [i for i, ms in se_to_mask if not _is_masked(ms)]
        om_ids = [i for i, ms in om_to_mask if not _is_masked(ms)]

        self.stdout.write(self.style.NOTICE(f"Cutoff: {cutoff.date()}  |  ShareEvent to mask: {len(se_ids)}  |  OutboundMessage to mask: {len(om_ids)}"))

        if opts["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Dry run: no changes made."))
            return

        with transaction.atomic():
            for sid in se_ids:
                se = ShareEvent.objects.select_for_update().get(id=sid)
                if not _is_masked(se.patient_msisdn):
                    se.patient_msisdn = _mask(se.patient_msisdn)
                    se.save(update_fields=["patient_msisdn"])

            for oid in om_ids:
                om = OutboundMessage.objects.select_for_update().get(id=oid)
                if not _is_masked(om.to_msisdn):
                    om.to_msisdn = _mask(om.to_msisdn)
                    meta = om.status_meta or {}
                    meta["masked_at"] = timezone.now().isoformat()
                    om.status_meta = meta
                    om.save(update_fields=["to_msisdn", "status_meta"])

        self.stdout.write(self.style.SUCCESS("Masking complete."))
