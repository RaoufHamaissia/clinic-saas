from django.db import models

from .querysets import ClinicQuerySet

class ClinicManager(models.Manager):

    def get_queryset(self) -> models.QuerySet:
        return ClinicQuerySet(self.model, using=self._db)

    def for_clinic(self, clinic):
        return self.get_queryset().for_clinic(clinic) #type:ignore

    