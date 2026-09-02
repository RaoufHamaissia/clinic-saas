from .models import (Prescription, PrescriptionItem, Medication, DoctorNote, ProcedureItem, ProcedureReport,
                    ProcedureReport, ProcedureItem, LabworkDemand, LabworkItem,
                     )
from django.db.models import Q

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

    @staticmethod
    def get_for_patient(clinic, patient, search=None, start_date=None, end_date=None):
        qs = Prescription.objects.for_clinic(clinic).filter(patient=patient).prefetch_related("items") #type:ignore

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        if search:
            search_lower = search.lower()
            matching_ids = [
                p.pk for p in qs
                if search_lower in (p.notes or "").lower()
                or any(search_lower in (item.medication_name or "").lower() for item in p.items.all())
            ]
            qs = qs.filter(pk__in=matching_ids)

        return qs

    

class DoctorNoteService:

    @staticmethod
    def create_note(*, clinic, patient, doctor, content):
        if patient.clinic_id != clinic.id:
            raise ValueError("Patient does not belong to this clinic.")

        if doctor.clinic_id != clinic.id:
            raise ValueError("Doctor does not belong to this clinic.")

        return DoctorNote.objects.create(
            clinic=clinic, patient=patient, doctor=doctor, content=content
        )

    @staticmethod
    def get_for_patient(clinic, patient, search=None, start_date=None, end_date=None):
        qs = DoctorNote.objects.for_clinic(clinic).filter(patient=patient) #type:ignore

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        if search:
            search_lower = search.lower()
            matching_ids = [n.pk for n in qs if search_lower in (n.content or "").lower()]
            qs = qs.filter(pk__in=matching_ids)

        return qs



class ProcedureReportService:

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

    @staticmethod
    def get_for_patient(clinic, patient, search=None, start_date=None, end_date=None):
        qs = ProcedureReport.objects.for_clinic(clinic).filter(patient=patient).prefetch_related("items") #type:ignore

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        if search:
            search_lower = search.lower()
            matching_ids = [
                r.pk for r in qs
                if search_lower in (r.notes or "").lower()
                or any(
                    search_lower in (item.procedure_name or "").lower()
                    or search_lower in (item.findings or "").lower()
                    for item in r.items.all()
                )
            ]
            qs = qs.filter(pk__in=matching_ids)

        return qs



class LabworkDemandService:

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

    @staticmethod
    def get_for_patient(clinic, patient, search=None, start_date=None, end_date=None):
        qs = LabworkDemand.objects.for_clinic(clinic).filter(patient=patient).prefetch_related("items") #type:ignore

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        if search:
            search_lower = search.lower()
            matching_ids = [
                d.pk for d in qs
                if any(
                    search_lower in (item.test_name or "").lower()
                    or search_lower in (item.clinical_indication or "").lower()
                    for item in d.items.all()
                )
            ]
            qs = qs.filter(pk__in=matching_ids)

        return qs