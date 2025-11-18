# registration/models.py (update)
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import secrets

User = get_user_model()

def _gen_token():
    return secrets.token_urlsafe(32)[:64]

class RegistrationLink(models.Model):
    token       = models.CharField(max_length=64, unique=True, db_index=True, blank=True)
    is_self     = models.BooleanField(default=True)
    # Sprint 2: campaign-bound links for field reps
    campaign    = models.ForeignKey("campaigns.Campaign", on_delete=models.CASCADE, null=True, blank=True, related_name="registration_links")
    label       = models.CharField(max_length=128, blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    expires_at  = models.DateTimeField(blank=True, null=True)
    max_uses    = models.PositiveIntegerField(default=0)     # 0 = unlimited (per-link cap)
    uses_count  = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = _gen_token()
        # link coherence
        if self.campaign_id and self.is_self:
            self.is_self = False
        return super().save(*args, **kwargs)

    @property
    def is_valid_now(self):
        if not self.is_active:
            return False
        now = timezone.now()
        if self.expires_at and now > self.expires_at:
            return False
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        # if campaign link → campaign must be active
        if self.campaign_id:
            c = self.campaign
            today = timezone.localdate()
            if not (c.is_active_flag and c.start_date <= today <= c.end_date):
                return False
        return True

    def mark_used(self):
        type(self).objects.filter(pk=self.pk).update(uses_count=models.F("uses_count") + 1)
        self.refresh_from_db(fields=["uses_count"])

    def __str__(self):
        if self.campaign_id:
            return f"CampaignLink[{self.campaign.brand.name}:{self.campaign.name}]"
        return f"SelfReg[{self.label or self.token}]"

class DoctorRegistration(models.Model):
    registration_link = models.ForeignKey(RegistrationLink, on_delete=models.SET_NULL, null=True, blank=True)
    doctor            = models.ForeignKey("accounts.Doctor", on_delete=models.SET_NULL, null=True, blank=True)
    clinic            = models.ForeignKey("clinics.Clinic", on_delete=models.SET_NULL, null=True, blank=True)
    # Sprint 2 additions:
    campaign          = models.ForeignKey("campaigns.Campaign", on_delete=models.SET_NULL, null=True, blank=True)
    fieldrep          = models.ForeignKey("accounts.FieldRep", on_delete=models.SET_NULL, null=True, blank=True)
    registered_via    = models.CharField(max_length=16, choices=[("self", "self"), ("fieldrep", "fieldrep")], default="self")

    is_new_doctor     = models.BooleanField(default=False)
    payload_snapshot  = models.JSONField(default=dict, blank=True)
    result            = models.CharField(max_length=32, default="success")  # success/duplicate/error/cap_reached
    ip                = models.GenericIPAddressField(null=True, blank=True)
    user_agent        = models.TextField(blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"RegAudit[{self.pk}]"
