# registration/models.py
from django.db import models
from core.models import TimeStampedModel
from campaigns.models import RegistrationLink

class DoctorRegistration(TimeStampedModel):
    """
    Audit log for both self and field-rep registrations.
    """
    registration_link = models.ForeignKey(RegistrationLink, on_delete=models.SET_NULL, null=True, blank=True)
    fieldrep = models.ForeignKey("accounts.FieldRep", on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey("accounts.Doctor", on_delete=models.SET_NULL, null=True, blank=True)
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.SET_NULL, null=True, blank=True)
    is_new_doctor = models.BooleanField(default=False)
    payload_snapshot = models.JSONField(default=dict)  # copy of submitted form
    result = models.CharField(max_length=32, default="success")  # success/duplicate/error
