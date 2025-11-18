# campaigns/models.py
from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel

class Campaign(TimeStampedModel):
    brand = models.ForeignKey("brands.Brand", on_delete=models.CASCADE, related_name="campaigns")
    name = models.CharField(max_length=128)
    therapy_area = models.ForeignKey("brands.TherapyArea", on_delete=models.PROTECT, related_name="campaigns")
    start_date = models.DateField()
    end_date = models.DateField()
    max_doctors = models.PositiveIntegerField(default=0)  # 0 = unlimited
    is_active_flag = models.BooleanField(default=True)

    class Meta:
        unique_together = [("brand", "name")]
        indexes = [models.Index(fields=["start_date", "end_date"])]

    @property
    def is_active(self):
        today = timezone.localdate()
        return self.is_active_flag and self.start_date <= today <= self.end_date

    @property
    def doctors_count(self):
        return self.doctor_tags.count()

    @property
    def capacity_left(self):
        if self.max_doctors == 0:
            return None  # unlimited
        return max(self.max_doctors - self.doctors_count, 0)

class CampaignSubtopic(TimeStampedModel):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="campaign_subtopics")
    subtopic = models.ForeignKey("content.Subtopic", on_delete=models.CASCADE, related_name="campaigns")

    class Meta:
        unique_together = [("campaign", "subtopic")]

class DoctorCampaign(TimeStampedModel):
    doctor = models.ForeignKey("accounts.Doctor", on_delete=models.CASCADE, related_name="campaign_tags")
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="doctor_tags")
    tagged_at = models.DateTimeField(auto_now_add=True)
    end_date_snapshot = models.DateField()  # snapshot of campaign end_date at tagging time
    registered_via = models.CharField(max_length=16, choices=[("self", "self"), ("fieldrep", "fieldrep")], default="fieldrep")
    fieldrep = models.ForeignKey("accounts.FieldRep", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = [("doctor", "campaign")]
        indexes = [models.Index(fields=["campaign", "tagged_at"])]
