# registration/models.py
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
import secrets

User = get_user_model()

def _gen_token():
    # 43~urlsafe chars; trim to max_length
    return secrets.token_urlsafe(32)[:64]

class RegistrationLink(models.Model):
    """
    Self-registration links have is_self=True (Sprint 1).
    Campaign-specific links will be added in Sprint 2.
    """
    token       = models.CharField(max_length=64, unique=True, db_index=True, blank=True)
    is_self     = models.BooleanField(default=True)
    label       = models.CharField(max_length=128, blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    expires_at  = models.DateTimeField(blank=True, null=True)
    max_uses    = models.PositiveIntegerField(default=0)     # 0 = unlimited
    uses_count  = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = _gen_token()
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
        return True

    def mark_used(self):
        # safe concurrent increment
        type(self).objects.filter(pk=self.pk).update(uses_count=models.F("uses_count") + 1)
        self.refresh_from_db(fields=["uses_count"])

    def __str__(self):
        return f"SelfReg[{self.label or self.token}]"

class DoctorRegistration(models.Model):
    """
    Audit every (self) registration submission.
    """
    registration_link = models.ForeignKey(RegistrationLink, on_delete=models.SET_NULL, null=True, blank=True)
    doctor            = models.ForeignKey("accounts.Doctor", on_delete=models.SET_NULL, null=True, blank=True)
    clinic            = models.ForeignKey("clinics.Clinic", on_delete=models.SET_NULL, null=True, blank=True)
    is_new_doctor     = models.BooleanField(default=False)
    payload_snapshot  = models.JSONField(default=dict, blank=True)
    result            = models.CharField(max_length=32, default="success")  # success/duplicate/error
    ip                = models.GenericIPAddressField(null=True, blank=True)
    user_agent        = models.TextField(blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"RegAudit[{self.pk}]"
