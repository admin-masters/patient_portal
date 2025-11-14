# core/models.py
from django.db import models
from django.utils.crypto import get_random_string

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Language(TimeStampedModel):
    code = models.CharField(max_length=8, unique=True)  # en, hi, te, ml, mr, kn, ta, bn
    name = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

def generate_public_id(prefix="C", length=7):
    return f"{prefix}{get_random_string(length=length).upper()}"

class PublicIdMixin(models.Model):
    public_id = models.CharField(max_length=16, unique=True, default=generate_public_id, editable=False, db_index=True)

    class Meta:
        abstract = True
