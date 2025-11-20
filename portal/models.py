# portal/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import TimeStampedModel

User = get_user_model()

class ClinicMember(TimeStampedModel):
    ROLE_CHOICES = (("doctor", "Doctor"), ("staff", "Staff"))

    user   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="clinic_memberships")
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.CASCADE, related_name="memberships")
    role   = models.CharField(max_length=16, choices=ROLE_CHOICES, default="doctor")
    # Optional: link this member to a Doctor record, if applicable
    doctor = models.ForeignKey("accounts.Doctor", on_delete=models.SET_NULL, null=True, blank=True, related_name="portal_members")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("user", "clinic")]
        indexes = [models.Index(fields=["clinic", "role", "is_active"])]

    def __str__(self):
        return f"{self.user} → {self.clinic} ({self.role})"
