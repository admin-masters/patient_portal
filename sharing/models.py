# sharing/models.py
from django.db import models
from core.models import TimeStampedModel, Language
from django.core.validators import RegexValidator

class ShareLink(TimeStampedModel):
    TYPE_CHOICES = [("video", "video"), ("subtopic", "subtopic"), ("portal", "portal")]
    token = models.CharField(max_length=24, unique=True, db_index=True)  # short URL token
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    doctor = models.ForeignKey("accounts.Doctor", on_delete=models.PROTECT)
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    video = models.ForeignKey("content.Video", on_delete=models.PROTECT, null=True, blank=True)
    subtopic = models.ForeignKey("content.Subtopic", on_delete=models.PROTECT, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["type", "clinic", "language"])]

class ShareEvent(TimeStampedModel):
    CHANNEL_CHOICES = [("whatsapp", "whatsapp"), ("email", "email")]
    type = models.CharField(max_length=16, choices=ShareLink.TYPE_CHOICES)
    doctor = models.ForeignKey("accounts.Doctor", on_delete=models.PROTECT)
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT)
    campaign = models.ForeignKey("campaigns.Campaign", on_delete=models.SET_NULL, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="language")
    video = models.ForeignKey("content.Video", on_delete=models.PROTECT, null=True, blank=True)
    subtopic = models.ForeignKey("content.Subtopic", on_delete=models.PROTECT, null=True, blank=True)
    patient_msisdn = models.CharField(
        max_length=10, validators=[RegexValidator(r"^\d{10}$")], db_index=True
    )
    share_link = models.OneToOneField(ShareLink, on_delete=models.PROTECT, related_name="share_event")
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES, default="whatsapp")
    message_preview = models.TextField(blank=True, null=True)  # stored copy of the message text

class LinkVisit(TimeStampedModel):
    share_link = models.ForeignKey(ShareLink, on_delete=models.CASCADE, related_name="visits")
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    referer = models.TextField(blank=True, null=True)
