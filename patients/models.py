from django.db import models
from core.models import ClinicOwnedModel
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class Patient(ClinicOwnedModel):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = PhoneNumberField(unique=True, blank=True)
    address = models.TextField(blank=True)

    reason_for_visit = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"