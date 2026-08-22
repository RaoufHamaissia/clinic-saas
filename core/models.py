from django.db import models
from .managers import ClinicManager


# Create your models here.

class ClinicOwnedModel(models.Model):
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT, related_name="%(class)s_set")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ClinicManager()
    class Meta:
        abstract = True