from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import User

from .models import Clinic, Specialty

from .profiles import DoctorProfile




class ClinicService:
    @staticmethod
    @transaction.atomic
    def create_clinic(
                        *,
                        clinic_name,
                        doctor_email,
                        password,
                        first_name,
                        last_name,
                        specialty,                    
                        clinic_phone="",
                        clinic_email="",
                        clinic_address="",
                        
    ):
        
        # 1. Create the clinic
        clinic = Clinic.objects.create(name=clinic_name,
                                        phone=clinic_phone,                                  
                                        address=clinic_address)


        # 2. Create the doctor User
        user = User.objects.create_clinic_admin( #type:ignore
            email=doctor_email,
            password=password,
            clinic=clinic,
            first_name=first_name,
            last_name=last_name
        )

        # 3. Create the doctor's professional profile
        doctor = DoctorProfile.objects.create(
            user=user,
            clinic=clinic,
            specialty=specialty
        )

        return clinic, doctor

    @staticmethod
    def validate_doctor_profile(*, user, clinic, specialty):
        if user.clinic_id != clinic.id:
            raise ValueError("The doctor user does not belong to this clinic.")

        if user.role != User.Role.DOCTOR:
            raise ValueError("The user must have the doctor role.")

        if not user.is_clinic_admin:
            raise ValueError("The doctor must be a clinic administrator.")

        if specialty is None:
            raise ValueError("A specialty is required.")




class SpecialtyService:

    @staticmethod
    def suggest(query, limit=10):
        query = (query or "").strip()

        if not query:
            return Specialty.objects.none()

        return Specialty.objects.filter(is_active=True, name__icontains=query)[:limit]

    @staticmethod
    def get_or_create(name):
        """
        Case-insensitive lookup/create, same pattern as records.MedicationService.
        Matches against ALL specialties regardless of is_active, so typing an
        existing-but-deactivated specialty's name reuses it rather than creating
        a duplicate — is_active status itself is left untouched either way.
        """
        name = (name or "").strip()

        if not name:
            return None

        existing = Specialty.objects.filter(name__iexact=name).first()
        if existing:
            return existing

        return Specialty.objects.create(name=name, is_active=True)
