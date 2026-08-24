from django.db import models
from core.models import ClinicOwnedModel


# Create your models here.

class DoctorDocumentProfile(models.Model):
    """
    Letterhead info printed on every generated document (prescriptions,
    reports, labwork demands...). Kept separate from clinics.DoctorProfile so that
    model stays about org structure, and this stays about print identity.
    signature/stamp are genuinely files (uploaded once, reused every print)
    - everything else in this app is structured data.
    """
    doctor = models.OneToOneField("clinics.DoctorProfile",
                                  on_delete=models.CASCADE, related_name="document_profile")

    professional_title = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)

    signature = models.ImageField(upload_to="doctors/signatures/", blank=True, null=True)
    stamp = models.ImageField(upload_to="doctors/stamps/", blank=True, null=True)

    def __str__(self):
        return f"Document profile for {self.doctor}"

class Prescription(ClinicOwnedModel):
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT,related_name="prescriptions")
    doctor = models.ForeignKey("clinics.DoctorProfile", on_delete=models.PROTECT, related_name="prescriptions")

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Prescription for {self.patient} — {self.created_at:%Y-%m-%d}"

