from .models import Prescription, PrescriptionItem

class PrescriptionService:

    @staticmethod
    def get_for_clinic(clinic):
        return Prescription.objects.for_clinic(clinic) #type:ignore

    @staticmethod
    def get_prescription(clinic, prescription_id):
        return Prescription.objects.for_clinic(clinic).get(pk=prescription_id) #type:ignore

    @staticmethod
    def create_prescription(*, clinic, patient, doctor, notes="", items):
        if patient.clinic_id != clinic.id:
            raise ValueError("Patient does not belong to this clinic.")

        if doctor.clinic_id != clinic.id:
            raise ValueError("Doctor does not belong to this clinic.")

        prescription = Prescription.objects.create(
            clinic=clinic, patient=patient, doctor=doctor, notes=notes
        )

        PrescriptionItem.objects.bulk_create([
            PrescriptionItem(prescription=prescription, **item) for item in items
        ])

        return prescription