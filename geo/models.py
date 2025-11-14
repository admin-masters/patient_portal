# geo/models.py
from django.db import models

class IndiaState(models.Model):
    name = models.CharField(max_length=64, unique=True)
    iso_code = models.CharField(max_length=8, unique=True)  # optional, for consistency

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
