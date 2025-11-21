# sharing/models.py
from django.db import models
from django.core.validators import RegexValidator
from core.models import TimeStampedModel, Language
import secrets

def _token(n=22):
    # 22 chars → short URL-safe token
    return secrets.token_urlsafe(16)[:n]

class ShareLink(TimeStampedModel):
    TYPE_CHOICES = [("video", "video"), ("subtopic", "subtopic"), ("portal", "portal")]

    token     = models.CharField(max_length=32, unique=True, db_index=True, default=_token)
    type      = models.CharField(max_length=16, choices=TYPE_CHOICES)
    doctor    = models.ForeignKey("accounts.Doctor", on_delete=models.PROTECT)
    clinic    = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT)
    language  = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    video     = models.ForeignKey("content.Video", on_delete=models.PROTECT, null=True, blank=True)
    subtopic  = models.ForeignKey("content.Subtopic", on_delete=models.PROTECT, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["type", "clinic", "language"])]

    def __str__(self):
        return f"{self.type}:{self.token}"

class ShareEvent(TimeStampedModel):
    CHANNEL_CHOICES = [("whatsapp", "whatsapp"), ("email", "email")]

    type      = models.CharField(max_length=16, choices=ShareLink.TYPE_CHOICES)
    doctor    = models.ForeignKey("accounts.Doctor", on_delete=models.PROTECT)
    clinic    = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT)
    language  = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    video     = models.ForeignKey("content.Video", on_delete=models.PROTECT, null=True, blank=True)
    subtopic  = models.ForeignKey("content.Subtopic", on_delete=models.PROTECT, null=True, blank=True)

    patient_msisdn = models.CharField(
        max_length=10,
        validators=[RegexValidator(r"^\d{10}$")],
        db_index=True
    )
    share_link = models.OneToOneField(ShareLink, on_delete=models.PROTECT, related_name="share_event")
    channel   = models.CharField(max_length=16, choices=CHANNEL_CHOICES, default="whatsapp")
    message_preview = models.TextField(blank=True, null=True)

class LinkVisit(TimeStampedModel):
    share_link = models.ForeignKey(ShareLink, on_delete=models.CASCADE, related_name="visits")
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip         = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    referer    = models.TextField(blank=True, null=True)
