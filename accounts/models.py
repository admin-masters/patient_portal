# accounts/models.py
from django.db import models
from core.models import TimeStampedModel, PublicIdMixin
from geo.models import IndiaState

class Doctor(PublicIdMixin, TimeStampedModel):
    full_name = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    whatsapp_number = models.CharField(max_length=10, unique=True)  # 10-digit, no country code
    imc_number = models.CharField(max_length=32, unique=True)       # hard unique
    clinic_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    state = models.ForeignKey(IndiaState, on_delete=models.PROTECT, related_name="doctors")
    photo_url = models.URLField(blank=True, null=True)  # store on S3; URL here

    def __str__(self):
        return f"Dr. {self.full_name} [{self.public_id}]"

class FieldRep(TimeStampedModel):
    brand = models.ForeignKey("brands.Brand", on_delete=models.CASCADE, related_name="field_reps")
    name = models.CharField(max_length=128, blank=True, null=True)
    phone_number = models.CharField(max_length=10, db_index=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        unique_together = [("brand", "phone_number")]
