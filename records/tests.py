from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from patients.models import Patient

from .models import Prescription, PrescriptionItem
from .services import PrescriptionService

# Create your tests here.

class PrescriptionServiceTests(TestCase):

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

    def test_create_prescription_with_items(self):
        prescription = PrescriptionService.create_prescription(
            clinic=self.clinic_a,
            patient=self.patient_a,
            doctor=self.doctor_a,
            notes="Take with food",
            items=[
                {"medication_name": "Amoxicillin", "dosage": "500mg", "frequency": "3x/day", "duration": "7 days", "instructions": ""},
                {"medication_name": "Paracetamol", "dosage": "1g", "frequency": "as needed", "duration": "", "instructions": "max 4/day"},
            ],
        )

        self.assertEqual(prescription.items.count(), 2) #type:ignore
        self.assertEqual(prescription.notes, "Take with food")
        self.assertEqual(prescription.clinic, self.clinic_a)

    def test_create_prescription_rejects_cross_clinic_patient(self):
        with self.assertRaises(ValueError):
            PrescriptionService.create_prescription(
                clinic=self.clinic_a,
                patient=self.patient_b,
                doctor=self.doctor_a,
                items=[],
            )

    def test_create_prescription_rejects_cross_clinic_doctor(self):
        with self.assertRaises(ValueError):
            PrescriptionService.create_prescription(
                clinic=self.clinic_a,
                patient=self.patient_a,
                doctor=self.doctor_b,
                items=[],
            )

    def test_get_for_clinic_only_returns_own_prescriptions(self):
        PrescriptionService.create_prescription(
            clinic=self.clinic_a, patient=self.patient_a, doctor=self.doctor_a, items=[]
        )
        PrescriptionService.create_prescription(
            clinic=self.clinic_b, patient=self.patient_b, doctor=self.doctor_b, items=[]
        )

        results = PrescriptionService.get_for_clinic(self.clinic_a)

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().clinic, self.clinic_a)


class PrescriptionViewTests(TestCase):

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

    def test_list_requires_login(self):
        response = self.client.get(reverse("records:prescription_list"))
        self.assertEqual(response.status_code, 302)

    def test_user_without_clinic_cannot_view_list(self):
        self.client.login(email="no-clinic@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("records:prescription_list"))

        self.assertEqual(response.status_code, 403)

    def test_add_prescription_creates_record_and_redirects_to_print(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        data = {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "notes": "",
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-medication_name": "Amoxicillin",
            "form-0-dosage": "500mg",
            "form-0-frequency": "3x/day",
            "form-0-duration": "7 days",
            "form-0-instructions": "",
            "form-1-medication_name": "",
            "form-1-dosage": "",
            "form-1-frequency": "",
            "form-1-duration": "",
            "form-1-instructions": "",
            "form-2-medication_name": "",
            "form-2-dosage": "",
            "form-2-frequency": "",
            "form-2-duration": "",
            "form-2-instructions": "",
        }

        response = self.client.post(reverse("records:prescription_add"), data)

        prescription = Prescription.objects.get(patient=self.patient)

        self.assertRedirects(
            response, reverse("records:prescription_print", args=[prescription.pk])
        )
        self.assertEqual(prescription.items.count(), 1) #type:ignore
        self.assertEqual(prescription.items.first().medication_name, "Amoxicillin") #type:ignore

    def test_print_returns_pdf(self):
        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        prescription = PrescriptionService.create_prescription(
            clinic=self.clinic_a, patient=self.patient, doctor=self.doctor,
            items=[{"medication_name": "Amoxicillin", "dosage": "", "frequency": "", "duration": "", "instructions": ""}],
        )

        response = self.client.get(reverse("records:prescription_print", args=[prescription.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_print_rejects_prescription_from_other_clinic(self):
        other_user = User.objects.create_user( #type:ignore
            email="doc-b@example.com", password="pw", clinic=self.clinic_b
        )
        other_doctor = DoctorProfile.objects.create(
            user=other_user, clinic=self.clinic_b, specialty=self.specialty
        )
        other_patient = Patient.objects.create(
            clinic=self.clinic_b, first_name="Jane", last_name="B"
        )
        other_prescription = PrescriptionService.create_prescription(
            clinic=self.clinic_b, patient=other_patient, doctor=other_doctor, items=[]
        )

        self.client.login(email="staff-a@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("records:prescription_print", args=[other_prescription.pk]))

        self.assertEqual(response.status_code, 404)