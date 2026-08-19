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
                        professional_title="",
                        registration_number="",
                        professional_phone="",
                        professional_email="",


    ):
        # 1. Create the clinic
        clinic = Clinic.objects.create(name=clinic_name,
                                        phone=clinic_phone,
                                        email=clinic_email, 
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
            specialty=specialty,
            professional_title=professional_title,
            registration_number=registration_number,
            professional_phone=professional_phone,
            professional_email=professional_email
        )

        return clinic, doctor
