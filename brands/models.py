# brands/models.py
from django.db import models
from core.models import TimeStampedModel

class Brand(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, unique=True)

    def __str__(self):
        return self.name

class TherapyArea(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, unique=True)

    def __str__(self):
        return self.name
