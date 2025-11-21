# messaging/models.py
from django.db import models
from core.models import TimeStampedModel, Language

class MessageTemplate(TimeStampedModel):
    """
    key:
      - share_video
      - share_subtopic
      - share_portal
    channel: whatsapp | email
    """
    key = models.CharField(max_length=64, db_index=True)
    channel = models.CharField(max_length=16, choices=[("whatsapp", "whatsapp"), ("email", "email")])
    description = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        unique_together = [("key", "channel")]

class MessageTemplateI18n(TimeStampedModel):
    template = models.ForeignKey(MessageTemplate, on_delete=models.CASCADE, related_name="i18n")
    language = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    body = models.TextField()  # use {{doctor_name}}, {{title}}, {{subtopic}}, {{link}}

    class Meta:
        unique_together = [("template", "language")]

class OutboundMessage(TimeStampedModel):
    share_event = models.ForeignKey("sharing.ShareEvent", on_delete=models.SET_NULL, null=True, blank=True, related_name="outbound_messages")
    to_msisdn   = models.CharField(max_length=10, db_index=True)
    channel     = models.CharField(max_length=16, choices=[("whatsapp", "whatsapp"), ("email", "email")])
    language    = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    template_key = models.CharField(max_length=64)
    body_rendered = models.TextField()

    provider_message_id = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=32, default="queued")  # queued/sent/delivered/failed
    status_meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["channel", "status", "created_at"])]
