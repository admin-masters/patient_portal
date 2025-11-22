# messaging/providers/sendgrid_mail.py
from typing import Tuple, Dict
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from ..models import OutboundMessage

def send_email_message(om: OutboundMessage) -> Tuple[str, Dict]:
    """
    Returns (provider_message_id, status_meta)
    """
    if not settings.SENDGRID_ENABLE:
        return ("dry-run", {"note": "SendGrid disabled; no external send"})

    if not om.to_email:
        raise ValueError("OutboundMessage.to_email is required for email channel.")

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    mail = Mail(
        from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
        to_emails=[om.to_email],
        subject="Patient Education Message",
        plain_text_content=om.body_rendered,
    )
    resp = sg.send(mail)
    # 202 accepted
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"SendGrid send failed: {resp.status_code} {resp.body}")

    # SendGrid does not return message-id in body; use header
    provider_id = resp.headers.get("X-Message-Id") or resp.headers.get("X-Message-ID") or "accepted"
    return provider_id, {"status_code": resp.status_code}
