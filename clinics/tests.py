from django.test import TestCase

from clinics.forms import ClinicRegistrationForm
# Create your tests here.


from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from clinics.services import ClinicService

from patients.models import Patient

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
                "specialty": self.specialty.pk,

            }
        )

        self.assertTrue(form.is_valid())


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