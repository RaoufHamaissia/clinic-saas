from django.db import models
from .managers import ClinicManager


# Create your models here.

class ClinicOwnedModel(models.Model):
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT)

    objects = ClinicManager()
    class Meta:
        abstract = True