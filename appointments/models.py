from django.db import models
from django.conf import settings

from core.models import ClinicOwnedModel

# Create your models here.

class Appointment(ClinicOwnedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ARRIVED = "arrived", "Arrived"
        WAITING = "waiting", "Waiting"
        WITH_DOCTOR = "with_doctor", "With doctor"
        DONE = "done", "Done"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No show"

    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="appointments")

    doctor = models.ForeignKey("clinics.DoctorProfile", on_delete=models.PROTECT, related_name="appointments")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_appointments")

    scheduled_at = models.DateTimeField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    is_walk_in = models.BooleanField(default=False)

    class Meta:
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"{self.patient} with {self.doctor} at {self.scheduled_at:%Y-%m-%d %H:%M}"  
    