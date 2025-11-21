# messaging/management/commands/seed_message_templates.py
from django.core.management.base import BaseCommand
from messaging.models import MessageTemplate, MessageTemplateI18n
from core.models import Language

TEMPLATES = {
    ("share_video", "whatsapp"): {
        "en": "Your doctor {{doctor_name}} has shared important information with you regarding {{title}}. Click on this link to view the information {{link}}",
        "hi": "आपके डॉक्टर {{doctor_name}} ने {{title}} से जुड़ी महत्वपूर्ण जानकारी साझा की है। देखने के लिए यहाँ क्लिक करें: {{link}}",
    },
    ("share_subtopic", "whatsapp"): {
        "en": "Your doctor {{doctor_name}} has shared important information with you regarding {{subtopic}}. Click on this link to view the information {{link}}",
        "hi": "आपके डॉक्टर {{doctor_name}} ने {{subtopic}} से जुड़ी महत्वपूर्ण जानकारी साझा की है। यहाँ देखें: {{link}}",
    },
    ("share_portal", "whatsapp"): {
        "en": "Your doctor {{doctor_name}} has shared their patient education service for your child, to help you ensure your child grows healthy and happy. Access it here: {{link}}",
        "hi": "आपके डॉक्टर {{doctor_name}} ने आपके बच्चे के लिए रोगी शिक्षा सेवा साझा की है ताकि आप उसके स्वस्थ और खुशहाल विकास में सहयोग कर सकें। यहाँ देखें: {{link}}",
    },
}

class Command(BaseCommand):
    help = "Seeds default message templates (EN + HI). Add more languages via admin."

    def handle(self, *args, **kwargs):
        # ensure languages exist (Sprint 0 command already seeds them)
        langs = set(Language.objects.values_list("code", flat=True))
        for (key, channel), bodies in TEMPLATES.items():
            tpl, _ = MessageTemplate.objects.get_or_create(key=key, channel=channel)
            for code, body in bodies.items():
                if code not in langs:
                    continue
                MessageTemplateI18n.objects.update_or_create(
                    template=tpl, language_id=code, defaults={"body": body}
                )
        self.stdout.write(self.style.SUCCESS("Message templates seeded."))
