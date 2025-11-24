from django.conf import settings
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OutboundMessage
from .tasks import send_outbound_message

logger = logging.getLogger(__name__)

@receiver(post_save, sender=OutboundMessage)
def auto_dispatch_outbound(sender, instance: OutboundMessage, created: bool, **kwargs):
    if not created:
        return
    if instance.channel == "whatsapp" and not getattr(settings, "WABA_ENABLE", False):
        logger.info("WABA disabled or not configured; skipping WhatsApp dispatch for %s", instance.pk)
        return

    # Channel gates
    if instance.channel == "whatsapp" and not settings.WABA_ENABLE:
        # In dry-run mode, mark as 'sent' instantly to simulate
        instance.status = "sent"
        instance.status_meta = {"note": "WABA disabled; dry-run local send"}
        instance.save(update_fields=["status", "status_meta"])
        return

    if instance.channel == "email" and not getattr(settings, "SENDGRID_ENABLE", False):
        logger.info("SendGrid disabled or not configured; skipping email dispatch for %s", instance.pk)
        instance.status = "sent"
        instance.status_meta = {"note": "SendGrid disabled; dry-run local send"}
        instance.save(update_fields=["status", "status_meta"])
        return

    # Enqueue task
    send_outbound_message.delay(instance.id)
