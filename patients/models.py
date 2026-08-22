from django.db import models
from core.models import ClinicOwnedModel

# Create your models here.

class Patient(ClinicOwnedModel):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.PhoneNumberField((""))

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"