from django.test import TestCase

# Create your tests here.


from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from clinics.services import ClinicService

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



        
