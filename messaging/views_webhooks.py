# messaging/views_webhooks.py
import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import OutboundMessage
import hmac, hashlib
from django.conf import settings

@csrf_exempt
@require_POST
def waba_webhook(request):
    """
    Accepts Meta Cloud webhook payloads.
    We handle minimal cases:
      - statuses: [{"id":"wamid...","status":"sent|delivered|read|failed", ...}]
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    # Meta formats: entry -> changes -> value -> statuses
    statuses = []
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                st = change.get("value", {}).get("statuses", [])
                statuses.extend(st)
    except Exception:
        pass

    # Also accept a flat {"statuses":[...]} for manual testing
    if not statuses and "statuses" in payload:
        statuses = payload["statuses"]

    updated = 0
    for st in statuses:
        msg_id = st.get("id") or st.get("message_id")
        status = st.get("status")
        if not msg_id or not status:
            continue
        try:
            om = OutboundMessage.objects.get(provider_message_id=msg_id, channel="whatsapp")
            # Map provider → our status
            if status in ("sent", "delivered", "read"):
                om.status = "delivered" if status != "read" else "delivered"
            elif status in ("failed", "failed_permanent"):
                om.status = "failed"
            else:
                continue
            meta = om.status_meta or {}
            meta["waba_event"] = st
            om.status_meta = meta
            om.save(update_fields=["status", "status_meta"])
            updated += 1
        except OutboundMessage.DoesNotExist:
            continue

    return JsonResponse({"ok": True, "updated": updated})

@csrf_exempt
@require_POST
def sendgrid_webhook(request):
    """
    SendGrid Event Webhook: payload is a list of events.
    Each event has 'event' ('processed','delivered','open','bounce','dropped','spamreport','unsubscribe','deferred'),
    and includes 'sg_message_id' (like 'XXXYY..-0').
    """
    try:
        events = json.loads(request.body.decode("utf-8"))
        if not isinstance(events, list):
            return HttpResponseBadRequest("Expected list")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    updated = 0
    for ev in events:
        status = ev.get("event")
        sg_id = ev.get("sg_message_id") or ev.get("smtp-id")
        if not sg_id or not status:
            continue

        # sg_message_id may include '-0'; strip suffix for matching if needed.
        prov_id = sg_id.split(".filter")[0]
        try:
            om = OutboundMessage.objects.get(provider_message_id__startswith=prov_id, channel="email")
        except OutboundMessage.DoesNotExist:
            continue

        if status in ("processed", "deferred"):
            new_status = "sent"
        elif status in ("delivered", "open"):
            new_status = "delivered"
        elif status in ("bounce", "dropped", "spamreport"):
            new_status = "failed"
        else:
            new_status = om.status

        meta = om.status_meta or {}
        meta.setdefault("sendgrid_events", []).append(ev)
        om.status = new_status
        om.status_meta = meta
        om.save(update_fields=["status", "status_meta"])
        updated += 1

    return JsonResponse({"ok": True, "updated": updated})

def _valid_meta_signature(request):
    secret = getattr(settings, "WABA_APP_SECRET", "")
    if not secret:
        return True  # disabled
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not sig.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), msg=request.body, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig.split("=",1)[1], expected)

@csrf_exempt
@require_POST
def waba_webhook(request):
    if not _valid_meta_signature(request):
        return HttpResponseBadRequest("Invalid signature")
    # ... existing body ...
