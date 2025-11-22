# messaging/providers/whatsapp.py
import os
import json
import requests
from django.conf import settings
from typing import Tuple, Dict
from ..models import OutboundMessage

def send_whatsapp_message(om: OutboundMessage) -> Tuple[str, Dict]:
    """
    Returns (provider_message_id, status_meta)
    """
    # Dry-run handled by signal (status set to 'sent')
    if not settings.WABA_ENABLE:
        return ("dry-run", {"note": "WABA disabled; no external send"})

    provider = (settings.WABA_PROVIDER or "meta").lower()
    if provider == "meta":
        return _send_meta_cloud(om)
    elif provider == "twilio":
        return _send_twilio(om)
    else:
        raise ValueError(f"Unknown WABA_PROVIDER: {provider}")

def _send_meta_cloud(om: OutboundMessage) -> Tuple[str, Dict]:
    """
    Meta WhatsApp Cloud API (simple text message).
    Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages
    """
    phone_number_id = settings.WABA_PHONE_NUMBER_ID
    token = settings.WABA_TOKEN
    if not (phone_number_id and token):
        raise RuntimeError("Meta WABA not configured (WABA_PHONE_NUMBER_ID / WABA_TOKEN).")

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": f"91{om.to_msisdn}",
        "type": "text",
        "text": {"body": om.body_rendered},
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
    if resp.status_code >= 400:
        raise RuntimeError(f"WABA send failed: {resp.status_code} {resp.text}")

    data = resp.json()
    # Typically: {"messages":[{"id":"wamid.HBg..."}]}
    msg_id = None
    try:
        msg_id = data["messages"][0]["id"]
    except Exception:
        pass
    if not msg_id:
        raise RuntimeError(f"WABA response missing message id: {data}")

    return msg_id, {"provider": "meta", "response": data}

def _send_twilio(om: OutboundMessage) -> Tuple[str, Dict]:
    """
    Twilio WhatsApp fallback (optional). Requires TWILIO_* envs.
    """
    from twilio.rest import Client

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    tok = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    if not (sid and tok):
        raise RuntimeError("Twilio not configured (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN).")

    client = Client(sid, tok)
    to = f"whatsapp:+91{om.to_msisdn}"
    m = client.messages.create(from_=from_whatsapp, to=to, body=om.body_rendered)
    # m.sid is the message id
    return m.sid, {"provider": "twilio"}
