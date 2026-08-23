from .models import Patient



class PatientService:
    @staticmethod
    def get_for_clinic(clinic):
        return Patient.objects.for_clinic(clinic) #type:ignore

    @staticmethod
    def get_patient(clinic, patient_id):
        return Patient.objects.for_clinic(clinic).get(pk=patient_id) #type:ignore

    @staticmethod
    def create_patient(*, clinic, first_name, last_name, date_of_birth=None,
                       phone="", address="", reason_for_visit=""):
        return Patient.objects.create(clinic=clinic, first_name=first_name,
                                      last_name=last_name, date_of_birth=date_of_birth,
                                      phone=phone, address=address,
                                      reason_for_visit=reason_for_visit)

    