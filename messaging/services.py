# messaging/services.py
import re
from typing import Dict
from django.core.exceptions import ObjectDoesNotExist
from .models import MessageTemplate, MessageTemplateI18n

_PLACEHOLDER = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")

def render_message(key: str, language_code: str, channel: str, context: Dict[str, str]) -> str:
    """
    Resolve template by (key, channel, language_code) and substitute {{placeholders}}.
    Fallback: English ('en') if target language missing.
    """
    try:
        tpl = MessageTemplate.objects.get(key=key, channel=channel)
    except ObjectDoesNotExist:
        raise ValueError(f"Template not found: {key}/{channel}")

    try:
        body = tpl.i18n.get(language_id=language_code).body
    except ObjectDoesNotExist:
        body = tpl.i18n.get(language_id="en").body  # fallback

    def repl(m):
        name = m.group(1)
        return str(context.get(name, ""))

    return _PLACEHOLDER.sub(repl, body)
