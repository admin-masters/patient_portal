from celery import shared_task
from django.db import transaction
from .models import OutboundMessage
from .providers.whatsapp import send_whatsapp_message
from .providers.sendgrid_mail import send_email_message

@shared_task(
    bind=True,
    max_retries=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def send_outbound_message(self, outbound_id: int):
    # 1) Lock and set 'sending'
    with transaction.atomic():
        om = (OutboundMessage.objects
              .select_for_update(skip_locked=True)
              .get(pk=outbound_id))
        if om.status in ("sent", "delivered"):
            return True
        if om.status == "sending":
            return True
        om.status = "sending"
        om.save(update_fields=["status"])

    # 2) Send outside the lock
    try:
        if om.channel == "whatsapp":
            provider_id, meta = send_whatsapp_message(om)
        elif om.channel == "email":
            provider_id, meta = send_email_message(om)
        else:
            raise ValueError(f"Unsupported channel: {om.channel}")

        with transaction.atomic():
            om = OutboundMessage.objects.select_for_update().get(pk=outbound_id)
            om.provider_message_id = provider_id
            om.status = "sent"
            om.status_meta = meta or {}
            om.save(update_fields=["provider_message_id", "status", "status_meta"])
        return True

    except Exception:
        # put back to 'queued' so Celery autoretry will re-pick
        with transaction.atomic():
            OutboundMessage.objects.filter(pk=outbound_id, status="sending").update(status="queued")
        raise
