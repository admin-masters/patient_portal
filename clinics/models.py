# clinics/models.py
from django.db import models
from core.models import TimeStampedModel
from core.models import Language
from geo.models import IndiaState

class Clinic(TimeStampedModel):
    name = models.CharField(max_length=128)  # may default to "Clinic of Dr. <name>"
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    state = models.ForeignKey(IndiaState, on_delete=models.PROTECT, related_name="clinics")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    default_language = models.ForeignKey(Language, on_delete=models.PROTECT, to_field="code", db_column="default_language", default="en")
    portal_slug = models.SlugField(max_length=64, unique=True)  # for whitelabeled portal routes
    logo_url = models.URLField(blank=True, null=True)
    primary_color = models.CharField(max_length=7, default="#1D4ED8")  # hex

    def __str__(self):
        return self.name

class DoctorClinic(TimeStampedModel):
    doctor = models.ForeignKey("accounts.Doctor", on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="members")
    is_primary = models.BooleanField(default=True)  # the owning/lead doctor
    role = models.CharField(max_length=32, default="doctor")  # doctor / staff

    class Meta:
        unique_together = [("doctor", "clinic")]
