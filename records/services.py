from .models import (Prescription, PrescriptionItem, Medication, DoctorNote, ProcedureItem, ProcedureReport,
                    ProcedureReport, ProcedureItem, LabworkDemand, LabworkItem,
                     )


class MedicationService:
    @staticmethod
    def suggest(query, limit=10):
        query = (query or "").strip()

        if not query:
            return Medication.objects.none()

        return Medication.objects.filter(name__icontains=query)[:limit]

    @staticmethod
    def register(name):
        """
        Records a medication name into the global suggestion list if it's
        new. Case-insensitive dedup so "Amoxicillin" and "amoxicillin"
        don't create two entries.
        """
        name = (name or "").strip()

        if not name:
            return None

        existing = Medication.objects.filter(name__iexact=name).first()

        if existing:
            return existing
        return Medication.objects.create(name=name)

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

        for item in items:
            MedicationService.register(item["medication_name"])

        return prescription


    

class DoctorNoteService:


    @staticmethod
    def get_for_clinic(clinic):
        return DoctorNote.objects.for_clinic(clinic) #type:ignore

    @staticmethod
    def get_note(clinic, note_id):
        return DoctorNote.objects.for_clinic(clinic).get(pk=note_id) #type:ignore

    @staticmethod
    def create_note(*, clinic, patient, doctor, content):
        if patient.clinic_id != clinic.id:
            raise ValueError("Patient does not belong to this clinic.")

        if doctor.clinic_id != clinic.id:
            raise ValueError("Doctor does not belong to this clinic.")

        return DoctorNote.objects.create(
            clinic=clinic, patient=patient, doctor=doctor, content=content
        )



class ProcedureReportService:

    @staticmethod
    def get_for_clinic(clinic):
        return ProcedureReport.objects.for_clinic(clinic) #type:ignore

    @staticmethod
    def get_report(clinic, report_id):
        return ProcedureReport.objects.for_clinic(clinic).get(pk=report_id) #type:ignore

    @staticmethod
    def create_report(*, clinic, patient, doctor, notes="", items):
        if patient.clinic_id != clinic.id:
            raise ValueError("Patient does not belong to this clinic.")

        if doctor.clinic_id != clinic.id:
            raise ValueError("Doctor does not belong to this clinic.")

        report = ProcedureReport.objects.create(
            clinic=clinic, patient=patient, doctor=doctor, notes=notes
        )

        ProcedureItem.objects.bulk_create([
            ProcedureItem(report=report, **item) for item in items
        ])

        return report


class LabworkDemandService:

    @staticmethod
    def get_for_clinic(clinic): 
        return LabworkDemand.objects.for_clinic(clinic) #type:ignore

    @staticmethod
    def get_demand(clinic, demand_id):
        return LabworkDemand.objects.for_clinic(clinic).get(pk=demand_id) #type:ignore

    @staticmethod
    def create_demand(*, clinic, patient, doctor, items):
        if patient.clinic_id != clinic.id:
            raise ValueError("Patient does not belong to this clinic.")

        if doctor.clinic_id != clinic.id:
            raise ValueError("Doctor does not belong to this clinic.")

        demand = LabworkDemand.objects.create(clinic=clinic, patient=patient, doctor=doctor)

        LabworkItem.objects.bulk_create([
            LabworkItem(demand=demand, **item) for item in items
        ])

        return demand