from django.conf import settings
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OutboundMessage
from .tasks import send_outbound_message
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
import hashlib

from .models import OutboundMessage
from .tasks import send_outbound_message

logger = logging.getLogger(__name__)

def _dedupe_key(instance: OutboundMessage) -> str:
    bucket = timezone.now().strftime("%Y%m%d%H")  # hour bucket
    base = f"{instance.channel}|{instance.to_msisdn or instance.to_email or ''}|{instance.template_key}|{instance.language_id}|{(instance.body_rendered or '').strip()}|{bucket}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

@receiver(pre_save, sender=OutboundMessage)
def set_dedupe(sender, instance: OutboundMessage, **kwargs):
    if not instance.dedupe_key:
        instance.dedupe_key = _dedupe_key(instance)

@receiver(post_save, sender=OutboundMessage)
def auto_dispatch_outbound(sender, instance: OutboundMessage, created: bool, **kwargs):
    if not created:
        return
    # Duplicate suppression (same bucket)
    exists = OutboundMessage.objects.filter(
        dedupe_key=instance.dedupe_key,
    ).exclude(pk=instance.pk).exists()
    if exists:
        instance.status = "sent"
        sm = instance.status_meta or {}
        sm["note"] = "duplicate-suppressed"
        instance.status_meta = sm
        instance.save(update_fields=["status", "status_meta"])
        return

    # Dry-run gates (unchanged); enqueue task if enabled
    from django.conf import settings
    if instance.channel == "whatsapp" and not settings.WABA_ENABLE:
        instance.status = "sent"; instance.status_meta = {"note": "WABA disabled; dry-run"}; instance.save(update_fields=["status","status_meta"]); return
    if instance.channel == "email" and not settings.SENDGRID_ENABLE:
        instance.status = "sent"; instance.status_meta = {"note": "SendGrid disabled; dry-run"}; instance.save(update_fields=["status","status_meta"]); return

    send_outbound_message.delay(instance.id)
