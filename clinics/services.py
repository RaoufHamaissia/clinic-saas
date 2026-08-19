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
                        email,
                        password,
                        first_name,
                        last_name,
                        specialty,
                        professional_title="",
                        registration_number="",
                        professional_phone="",
                        professional_email="",

    ):
        clinic = Clinic.objects.create(name=clinic_name)

        user = User.objects.create_clinic_admin( #type:ignore
            email=email,
            password=password,
            clinic=clinic,
            first_name=first_name,
            last_name=last_name
        )

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
