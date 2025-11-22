# messaging/tasks.py
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import OutboundMessage

from .providers.whatsapp import send_whatsapp_message
from .providers.sendgrid_mail import send_email_message

@shared_task(
    bind=True,
    max_retries=5,
    autoretry_for=(Exception,),
    retry_backoff=True,          # exponential backoff: 1s, 2s, 4s, ...
    retry_backoff_max=600,       # cap at 10 minutes
    retry_jitter=True,
)
def send_outbound_message(self, outbound_id: int):
    om = OutboundMessage.objects.get(pk=outbound_id)

    try:
        if om.channel == "whatsapp":
            provider_id, meta = send_whatsapp_message(om)
        elif om.channel == "email":
            provider_id, meta = send_email_message(om)
        else:
            raise ValueError(f"Unsupported channel: {om.channel}")

        om.provider_message_id = provider_id
        om.status = "sent"
        om.status_meta = meta or {}
        om.save(update_fields=["provider_message_id", "status", "status_meta"])
        return True

    except Exception as e:
        # Let Celery retry (autoretry_for captures)
        raise
