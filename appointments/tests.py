from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from patients.models import Patient

from .models import Appointment
from .services import AppointmentService


class AppointmentServiceTests(TestCase):

    def setUp(self):
        self.clinic_a = Clinic.objects.create(name="Clinic A")
        self.clinic_b = Clinic.objects.create(name="Clinic B")
        self.specialty = Specialty.objects.create(name="General Medicine")

        self.doctor_user_a = User.objects.create_user( #type:ignore
            email="doc-a@example.com", password="pw", clinic=self.clinic_a
        )
        self.doctor_a = DoctorProfile.objects.create(
            user=self.doctor_user_a, clinic=self.clinic_a, specialty=self.specialty
        )

        self.doctor_user_b = User.objects.create_user( #type:ignore
            email="doc-b@example.com", password="pw", clinic=self.clinic_b
        )
        self.doctor_b = DoctorProfile.objects.create(
            user=self.doctor_user_b, clinic=self.clinic_b, specialty=self.specialty
        )

        self.patient_a = Patient.objects.create(
            clinic=self.clinic_a, first_name="John", last_name="A"
        )
        self.patient_b = Patient.objects.create(
            clinic=self.clinic_b, first_name="Jane", last_name="B"
        )

    def test_create_appointment_defaults_to_scheduled(self):
        appt = AppointmentService.create_appointment(
            clinic=self.clinic_a,
            patient=self.patient_a,
            doctor=self.doctor_a,
            scheduled_at=timezone.now() + timedelta(days=1),
            created_by=self.doctor_user_a,
        )

        self.assertEqual(appt.status, Appointment.Status.SCHEDULED)
        self.assertFalse(appt.is_walk_in)

    def test_create_walk_in_defaults_to_waiting(self):
        appt = AppointmentService.create_walk_in(
            clinic=self.clinic_a,
            patient=self.patient_a,
            doctor=self.doctor_a,
            created_by=self.doctor_user_a,
        )

        self.assertEqual(appt.status, Appointment.Status.WAITING)
        self.assertTrue(appt.is_walk_in)

    def test_cannot_book_appointment_with_cross_clinic_doctor(self):
        with self.assertRaises(ValueError):
            AppointmentService.create_appointment(
                clinic=self.clinic_a,
                patient=self.patient_a,
                doctor=self.doctor_b,
                scheduled_at=timezone.now() + timedelta(days=1),
                created_by=self.doctor_user_a,
            )

    def test_cannot_book_appointment_with_cross_clinic_patient(self):
        with self.assertRaises(ValueError):
            AppointmentService.create_appointment(
                clinic=self.clinic_a,
                patient=self.patient_b,
                doctor=self.doctor_a,
                scheduled_at=timezone.now() + timedelta(days=1),
                created_by=self.doctor_user_a,
            )

    def test_cannot_book_appointment_in_the_past(self):
        with self.assertRaises(ValidationError):
            AppointmentService.create_appointment(
                clinic=self.clinic_a,
                patient=self.patient_a,
                doctor=self.doctor_a,
                scheduled_at=timezone.now() - timedelta(days=1),
                created_by=self.doctor_user_a,
            )

        self.assertEqual(Appointment.objects.count(), 0)

    def test_get_for_day_only_returns_own_clinic(self):
        AppointmentService.create_walk_in(
            clinic=self.clinic_a, patient=self.patient_a,
            doctor=self.doctor_a, created_by=self.doctor_user_a,
        )
        AppointmentService.create_walk_in(
            clinic=self.clinic_b, patient=self.patient_b,
            doctor=self.doctor_b, created_by=self.doctor_user_b,
        )

        today_a = AppointmentService.get_for_day(self.clinic_a, timezone.localdate())

        self.assertEqual(today_a.count(), 1)
        self.assertEqual(today_a.first().clinic, self.clinic_a)

    def test_get_for_day_includes_both_scheduled_and_walk_in(self):
        today_noon = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)

        AppointmentService.create_appointment(
            clinic=self.clinic_a, patient=self.patient_a, doctor=self.doctor_a,
            scheduled_at=today_noon + timedelta(hours=1), created_by=self.doctor_user_a,
        )
        AppointmentService.create_walk_in(
            clinic=self.clinic_a, patient=self.patient_a,
            doctor=self.doctor_a, created_by=self.doctor_user_a,
        )

        today_a = AppointmentService.get_for_day(self.clinic_a, timezone.localdate())

        self.assertEqual(today_a.count(), 2)

    def test_update_status_rejects_invalid_value(self):
        appt = AppointmentService.create_walk_in(
            clinic=self.clinic_a, patient=self.patient_a,
            doctor=self.doctor_a, created_by=self.doctor_user_a,
        )

        with self.assertRaises(ValueError):
            AppointmentService.update_status(appointment=appt, new_status="not_a_real_status")

    def test_update_status_accepts_valid_value(self):
        appt = AppointmentService.create_walk_in(
            clinic=self.clinic_a, patient=self.patient_a,
            doctor=self.doctor_a, created_by=self.doctor_user_a,
        )

        AppointmentService.update_status(appointment=appt, new_status=Appointment.Status.WITH_DOCTOR)

        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.WITH_DOCTOR)


class AppointmentViewTests(TestCase):

    def setUp(self):
        self.clinic_a = Clinic.objects.create(name="Clinic A")
        self.clinic_b = Clinic.objects.create(name="Clinic B")
        self.specialty = Specialty.objects.create(name="General Medicine")

        self.user = User.objects.create_user( #type:ignore
            email="staff-a@example.com", password="StrongPassword123!", clinic=self.clinic_a
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.user, clinic=self.clinic_a, specialty=self.specialty
        )
        self.patient = Patient.objects.create(
            clinic=self.clinic_a, first_name="John", last_name="A"
        )

        self.no_clinic_user = User.objects.create_user( #type:ignore
            email="no-clinic@example.com", password="StrongPassword123!"
        )

    def test_day_view_requires_login(self):
        response = self.client.get(reverse("appointments:day"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url) #type:ignore

    def test_user_without_clinic_cannot_view_day(self):
        self.client.login(email="no-clinic@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("appointments:day"))

        self.assertEqual(response.status_code, 403)

    def test_user_without_clinic_cannot_add_appointment(self):
        self.client.login(email="no-clinic@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("appointments:add"))

        self.assertEqual(response.status_code, 403)

    def test_add_walk_in_creates_waiting_appointment(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.post(
            reverse("appointments:walk_in"),
            {"patient": self.patient.pk, "doctor": self.doctor.pk},
        )

        self.assertRedirects(response, reverse("appointments:day"))

        appt = Appointment.objects.get(patient=self.patient)
        self.assertEqual(appt.status, Appointment.Status.WAITING)
        self.assertTrue(appt.is_walk_in)

    def test_add_appointment_with_future_date_succeeds(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        future = timezone.now() + timedelta(days=1)

        response = self.client.post(
            reverse("appointments:add"),
            {
                "patient": self.patient.pk,
                "doctor": self.doctor.pk,
                "scheduled_at": future.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertRedirects(response, reverse("appointments:day"))
        self.assertEqual(Appointment.objects.filter(patient=self.patient).count(), 1)

    def test_add_appointment_with_past_date_fails(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        past = timezone.now() - timedelta(days=1)

        response = self.client.post(
            reverse("appointments:add"),
            {
                "patient": self.patient.pk,
                "doctor": self.doctor.pk,
                "scheduled_at": past.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertIn("scheduled_at", response.context["form"].errors)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_add_appointment_form_only_lists_own_clinic_patients_and_doctors(self):
        other_specialty = Specialty.objects.create(name="Cardiology")
        other_user = User.objects.create_user( #type:ignore
            email="doc-b@example.com", password="pw", clinic=self.clinic_b
        )
        other_doctor = DoctorProfile.objects.create(
            user=other_user, clinic=self.clinic_b, specialty=other_specialty
        )
        Patient.objects.create(clinic=self.clinic_b, first_name="Jane", last_name="B")

        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("appointments:add"))

        form = response.context["form"]
        self.assertIn(self.patient, form.fields["patient"].queryset)
        self.assertIn(self.doctor, form.fields["doctor"].queryset)
        self.assertNotIn(other_doctor, form.fields["doctor"].queryset)

    def test_update_status_via_post(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        appt = AppointmentService.create_walk_in(
            clinic=self.clinic_a, patient=self.patient,
            doctor=self.doctor, created_by=self.user,
        )

        response = self.client.post(
            reverse("appointments:update_status", args=[appt.pk]),
            {"status": Appointment.Status.WITH_DOCTOR},
        )

        self.assertRedirects(response, reverse("appointments:day"))

        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.WITH_DOCTOR)

    def test_update_status_rejects_appointment_from_other_clinic(self):
        other_specialty = Specialty.objects.create(name="Cardiology")
        other_user = User.objects.create_user( #type:ignore
            email="doc-b@example.com", password="pw", clinic=self.clinic_b
        )
        other_doctor = DoctorProfile.objects.create(
            user=other_user, clinic=self.clinic_b, specialty=other_specialty
        )
        other_patient = Patient.objects.create(
            clinic=self.clinic_b, first_name="Jane", last_name="B"
        )
        other_appt = AppointmentService.create_walk_in(
            clinic=self.clinic_b, patient=other_patient,
            doctor=other_doctor, created_by=other_user,
        )

        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.post(
            reverse("appointments:update_status", args=[other_appt.pk]),
            {"status": Appointment.Status.WITH_DOCTOR},
        )

        self.assertEqual(response.status_code, 404)

        other_appt.refresh_from_db()
        self.assertEqual(other_appt.status, Appointment.Status.WAITING)

    def test_add_appointment_prefills_patient_from_query_param(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("appointments:add") + f"?patient={self.patient.pk}")

        self.assertEqual(str(response.context["form"].initial.get("patient")), str(self.patient.pk))

    def test_add_appointment_redirects_to_next_when_provided(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        future = timezone.now() + timedelta(days=1)
        next_path = f"/patients/{self.patient.pk}/"

        response = self.client.post(reverse("appointments:add"), {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "scheduled_at": future.strftime("%Y-%m-%dT%H:%M"),
            "next": next_path,
        })

        self.assertRedirects(response, next_path, fetch_redirect_response=False)