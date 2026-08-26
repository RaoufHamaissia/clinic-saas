from django.test import TestCase

from clinics.forms import ClinicRegistrationForm
# Create your tests here.


from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from clinics.services import ClinicService

from patients.models import Patient

from django.urls import reverse

class ClinicServiceTests(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="General Medicine")

    def test_create_clinic_creates_doctor_admin(self):
        clinic, doctor = ClinicService.create_clinic(
            clinic_name="My Medical Clinic",
            doctor_email="doctor@example.com",
            password="StrongPassword123!",
            first_name="John",
            last_name="Doe",
            specialty=self.specialty
        )
        user = doctor.user

        self.assertIsNotNone(clinic)
        self.assertIsNotNone(doctor)

        

        self.assertEqual(clinic.name, "My Medical Clinic")

        self.assertEqual(user.email, "doctor@example.com")

        self.assertEqual(user.role, user.Role.DOCTOR)

        self.assertTrue(user.is_clinic_admin)

        self.assertEqual(user.clinic, clinic)

        self.assertEqual(doctor.clinic, clinic)

        self.assertEqual(doctor.specialty, self.specialty)

        self.assertTrue(user.check_password("StrongPassword123!"))



class ClinicRegistrationFormTests(TestCase):

    def setUp(self):
        self.specialty = Specialty.objects.create(name="General Medicine")

    def test_valid_registration_form(self):
        form = ClinicRegistrationForm(
            data={
                "clinic_name": "My Clinic",
                "clinic_phone": "0555123456",
                "clinic_address": "Annaba",
                "first_name": "John",
                "last_name": "Doe",
                "email": "doctor@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "specialty": self.specialty.name,   # <-- was self.specialty.pk
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["specialty"], self.specialty)

    def test_registration_reuses_existing_specialty_case_insensitively(self):
        form = ClinicRegistrationForm(
            data={
                "clinic_name": "My Clinic",
                "clinic_phone": "",
                "clinic_address": "",
                "first_name": "John",
                "last_name": "Doe",
                "email": "doctor2@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "specialty": "general medicine",   # different case
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["specialty"], self.specialty)
        self.assertEqual(Specialty.objects.filter(name__iexact="general medicine").count(), 1)

    def test_registration_creates_new_specialty_if_not_found(self):
        form = ClinicRegistrationForm(
            data={
                "clinic_name": "My Clinic",
                "clinic_phone": "",
                "clinic_address": "",
                "first_name": "John",
                "last_name": "Doe",
                "email": "doctor3@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "specialty": "Dermatology",
            }
        )

        self.assertTrue(form.is_valid())

        specialty = form.cleaned_data["specialty"]
        self.assertEqual(specialty.name, "Dermatology")
        self.assertTrue(Specialty.objects.filter(name="Dermatology", is_active=True).exists())

    def test_registration_requires_specialty(self):
        form = ClinicRegistrationForm(
            data={
                "clinic_name": "My Clinic",
                "first_name": "John",
                "last_name": "Doe",
                "email": "doctor4@example.com",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "specialty": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("specialty", form.errors)


class SpecialtySuggestViewTests(TestCase):

    def setUp(self):
        Specialty.objects.create(name="Cardiology", is_active=True)
        Specialty.objects.create(name="Dermatology", is_active=True)
        Specialty.objects.create(name="Retired Specialty", is_active=False)

    def test_suggest_works_without_login(self):
        response = self.client.get(reverse("clinics:specialty_suggest"), {"q": "cardio"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": ["Cardiology"]})

    def test_suggest_excludes_inactive_specialties(self):
        response = self.client.get(reverse("clinics:specialty_suggest"), {"q": "retired"})

        self.assertEqual(response.json(), {"results": []})

    def test_suggest_returns_empty_for_blank_query(self):
        response = self.client.get(reverse("clinics:specialty_suggest"), {"q": ""}) #type:ignore

        self.assertEqual(response.json(), {"results": []})

class TenantIsolationTests(TestCase):

    def setUp(self):
        self.clinic_a = Clinic.objects.create(name="Clinic A")
        self.clinic_b = Clinic.objects.create(name="Clinic B")

        self.patient_a = Patient.objects.create(clinic=self.clinic_a, first_name="John", last_name="Patient")
        self.patient_b = Patient.objects.create(clinic=self.clinic_b, first_name="Jane", last_name="Patient")

    def test_clinic_a_only_gets_its_patients(self):
        patients = Patient.objects.for_clinic(self.clinic_a) #type:ignore

        self.assertEqual( patients.count(), 1)
        self.assertEqual( patients.first(), self.patient_a)
        self.assertNotIn( self.patient_b, patients)
        

    def test_clinic_b_only_gets_its_patients(self): 

        patients = Patient.objects.for_clinic( self.clinic_b )  #type:ignore

        self.assertEqual( patients.count(), 1, ) 
        self.assertEqual( patients.first(), self.patient_b, ) 
        self.assertNotIn( self.patient_a, patients, )