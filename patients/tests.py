from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from appointments.services import AppointmentService
from records.services import PrescriptionService
from .models import Patient


# Create your tests here.

class PatientViewTests(TestCase):

    def setUp(self):
        self.clinic_a = Clinic.objects.create(name="Clinic A")
        self.clinic_b = Clinic.objects.create(name="Clinic B")

        self.user_a = User.objects.create_user( #type:ignore
            email="staff-a@example.com",
            password="StrongPassword123!",
            clinic=self.clinic_a,
        )

        self.user_b = User.objects.create_user( #type:ignore
            email="staff-b@example.com",
            password="StrongPassword123!",
            clinic=self.clinic_b,
        )

        self.no_clinic_user = User.objects.create_user( #type:ignore
            email="no-clinic@example.com",
            password="StrongPassword123!",
        )

        self.patient_a = Patient.objects.create(
            clinic=self.clinic_a, first_name="John", last_name="A"
        )
        self.patient_b = Patient.objects.create(
            clinic=self.clinic_b, first_name="Jane", last_name="B"
        )

    def test_list_requires_login(self):
        response = self.client.get(reverse("patients:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url) #type:ignore

    def test_list_only_shows_own_clinic_patients(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!") 

        response = self.client.get(reverse("patients:list"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.patient_a, response.context["patients"])
        self.assertNotIn(self.patient_b, response.context["patients"])

    def test_user_without_clinic_cannot_view_list(self):
        self.client.login(email="no-clinic@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("patients:list"))

        self.assertEqual(response.status_code, 403)

    def test_user_without_clinic_cannot_add_patient(self):
        self.client.login(email="no-clinic@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("patients:add"))

        self.assertEqual(response.status_code,  403)

    def test_add_patient_creates_patient_for_users_clinic(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.post(
            reverse("patients:add"), 
            {
                "first_name": "New",
                "last_name": "Patient",
                "phone": "",
                "address": "",
                "reason_for_visit": "Check-up",  
            },
        )

        self.assertRedirects(response, reverse("patients:list"))

        patient = Patient.objects.get(first_name="New", last_name="Patient")
        self.assertEqual(patient.clinic, self.clinic_a)
        self.assertEqual(patient.reason_for_visit, "Check-up")

    def test_add_patient_form_requires_first_and_last_name(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.post(reverse("patients:add"),
                                    {
                                        "first_name": "",
                                        "last_name": "",
                                    })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertIn("first_name", response.context["form"].errors)
        self.assertIn("last_name", response.context["form"].errors)


class PatientDetailViewTests(TestCase):

    def setUp(self):
        self.clinic_a = Clinic.objects.create(name="Clinic A")
        self.clinic_b = Clinic.objects.create(name="Clinic B")
        self.specialty = Specialty.objects.create(name="General Medicine")

        self.user = User.objects.create_user(
            email="staff-a@example.com", password="StrongPassword123!", clinic=self.clinic_a
        ) #type:ignore
        self.doctor = DoctorProfile.objects.create(
            user=self.user, clinic=self.clinic_a, specialty=self.specialty
        )

        self.patient = Patient.objects.create(clinic=self.clinic_a, first_name="John", last_name="A")
        self.other_clinic_patient = Patient.objects.create(clinic=self.clinic_b, first_name="Jane", last_name="B")

    def test_detail_requires_login(self):
        response = self.client.get(reverse("patients:detail", args=[self.patient.pk]))
        self.assertEqual(response.status_code, 302)

    def test_detail_shows_aggregated_records(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        AppointmentService.create_walk_in(
            clinic=self.clinic_a, patient=self.patient, doctor=self.doctor, created_by=self.user
        )
        PrescriptionService.create_prescription(
            clinic=self.clinic_a, patient=self.patient, doctor=self.doctor, items=[]
        )

        response = self.client.get(reverse("patients:detail", args=[self.patient.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["appointments"].count(), 1)
        self.assertEqual(response.context["prescriptions"].count(), 1)
        self.assertEqual(response.context["notes"].count(), 0)

    def test_detail_404_for_patient_in_other_clinic(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("patients:detail", args=[self.other_clinic_patient.pk]))

        self.assertEqual(response.status_code, 404)