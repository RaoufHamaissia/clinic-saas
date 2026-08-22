from .models import Patient



class PatientService:
    @staticmethod
    def get_for_clinic(clinic):
        return Patient.objects.for_clinic(clinic) #type:ignore

    @staticmethod
    def get_patient(clinic, patient_id):
        return Patient.objects.for_clinic(clinic).get(pk=patient_id) #type:ignore