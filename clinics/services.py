from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.models import User

from .models import Clinic
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



