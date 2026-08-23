from hmac import new

from django.utils import timezone

from .models import Appointment

class AppointmentService:

    @staticmethod
    def get_for_day(clinic, day):
        return (
            Appointment.objects
            .for_clinic(scheduled_at__date=day)   #type:ignore
            .select_related("patient", "doctor__user")
        )

    @staticmethod
    def create_appointment(*, clinic, patient, doctor, scheduled_at, created_by):
        if patient.clinic_id != clinic.id:
            raise ValueError("Patient does not belong to this clinic.")

        if doctor.clinic_id != clinic.id:
            raise ValueError("Doctor does not belong to this clinic.")

        return Appointment.objects.create(
            clinic=clinic,
            patient=patient,
            doctor=doctor,
            scheduled_at=scheduled_at,
            status=Appointment.Status.SCHEDULED,
            is_walk_in=False,
            created_by=created_by
        )

    @staticmethod
    def create_walk_in(*, clinic, patient, doctor, created_by):
        if patient.clinic_id != clinic.id:
            raise ValueError("Patient does not belong to this clinic.")
        
        if doctor.clinic_id != clinic.id:
            raise ValueError("Doctor does not belong to this clinic.")

        return Appointment.objects.create(
                    clinic=clinic,
                    patient=patient,
                    doctor=doctor,
                    scheduled_at=timezone.now(),
                    status=Appointment.Status.SCHEDULED,
                    is_walk_in=True,
                    created_by=created_by
                )

    @staticmethod
    def update_status(*, appointment, new_status):
        valid_statuses = dict(Appointment.Status.choices)

        if new_status not in valid_statuses:
            raise ValueError("Invalid status.")

        appointment.status = new_status 
        appointment.save(update_fields=["status", "updated_at"])

        return appointment