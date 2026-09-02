from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from patients.models import Patient

from .models import AuditLog
from .services import AuditLogService

# Create your tests here.


class AuditLogServiceTests(TestCase):

    def setUp(self):
        self.clinic = Clinic.objects.create(name="Clinic A")
        self.user = User.objects.create_user(email="doc@example.com", password="pw", clinic=self.clinic) #type:ignore

    def test_log_creates_entry_with_target(self):
        patient = Patient.objects.create(clinic=self.clinic, first_name="John", last_name="A")

        AuditLogService.log(
            actor=self.user, clinic=self.clinic, action=AuditLogService.Action.PRINT, target=patient
        )

        entry = AuditLog.objects.latest("created_at")
        self.assertEqual(entry.action, "print")
        self.assertEqual(entry.actor_email, "doc@example.com")
        self.assertEqual(entry.content_type, ContentType.objects.get_for_model(Patient))
        self.assertEqual(entry.object_id, patient.pk)
        self.assertIn("John", entry.object_repr)

    def test_get_all_filters_by_action(self):
        AuditLogService.log(actor=self.user, clinic=self.clinic, action=AuditLogService.Action.LOGIN)
        AuditLogService.log(actor=self.user, clinic=self.clinic, action=AuditLogService.Action.LOGOUT)

        results = AuditLogService.get_all({"action": "login"})

        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().action, "login")


class ModelChangeAuditSignalTests(TestCase):

    def test_creating_patient_logs_create_action(self):
        clinic = Clinic.objects.create(name="Clinic A")

        Patient.objects.create(clinic=clinic, first_name="John", last_name="A")

        entry = AuditLog.objects.filter(action="create", content_type__model="patient").latest("created_at")
        self.assertIn("John", entry.object_repr)

    def test_updating_patient_logs_update_action(self):
        clinic = Clinic.objects.create(name="Clinic A")
        patient = Patient.objects.create(clinic=clinic, first_name="John", last_name="A")

        patient.first_name = "Jonathan"
        patient.save()

        entry = AuditLog.objects.filter(action="update", content_type__model="patient").latest("created_at")
        self.assertIn("Jonathan", entry.object_repr)


class LoginAuditSignalTests(TestCase):

    def setUp(self):
        self.clinic = Clinic.objects.create(name="Clinic A")
        self.user = User.objects.create_user( #type:ignore
            email="doc@example.com", password="StrongPassword123!", clinic=self.clinic
        )

    def test_successful_login_logs_login_action(self):
        self.client.login(email="doc@example.com", password="StrongPassword123!")

        entry = AuditLog.objects.filter(action="login").latest("created_at")
        self.assertEqual(entry.actor_email, "doc@example.com")

    def test_failed_login_logs_login_failed_action(self):
        self.client.post(reverse("accounts:login"), {
            "email": "doc@example.com", "password": "WrongPassword",
        })

        entry = AuditLog.objects.filter(action="login_failed").latest("created_at")
        self.assertIsNone(entry.actor)
        self.assertIn("doc@example.com", entry.object_repr)


class AuditTrailMiddlewareTests(TestCase):

    def setUp(self):
        self.clinic = Clinic.objects.create(name="Clinic A")
        self.user = User.objects.create_user( #type:ignore
            email="doc@example.com", password="StrongPassword123!", clinic=self.clinic
        )

    def test_authenticated_request_logs_view_action(self):
        self.client.login(email="doc@example.com", password="StrongPassword123!")

        self.client.get(reverse("core:dashboard"))

        entry = AuditLog.objects.filter(action="view", path="/dashboard/").latest("created_at")
        self.assertEqual(entry.status_code, 200)

    def test_unauthenticated_request_does_not_log(self):
        self.client.get(reverse("accounts:login"))

        self.assertFalse(AuditLog.objects.filter(action="view").exists())


class AuditLogViewTests(TestCase):

    def setUp(self):
        self.clinic = Clinic.objects.create(name="Clinic A")

        self.regular_user = User.objects.create_user( #type:ignore
            email="doc@example.com", password="StrongPassword123!", clinic=self.clinic
        )

        self.superuser = User.objects.create_superuser( #type:ignore
            email="admin@platform.com", password="StrongPassword123!"
        )

    def test_regular_user_cannot_access_audit_log(self):
        self.client.login(email="doc@example.com", password="StrongPassword123!")

        response = self.client.get(reverse("core:audit_log"))

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access_audit_log(self):
        self.client.login(email="admin@platform.com", password="StrongPassword123!")

        response = self.client.get(reverse("core:audit_log"))

        self.assertEqual(response.status_code, 200)


class PrescriptionPrintAuditTests(TestCase):

    def test_printing_prescription_logs_print_action(self):
        from records.services import PrescriptionService

        clinic = Clinic.objects.create(name="Clinic A")
        specialty = Specialty.objects.create(name="General Medicine")
        user = User.objects.create_user(email="doc@example.com", password="StrongPassword123!", clinic=clinic) #type:ignore
        doctor = DoctorProfile.objects.create(user=user, clinic=clinic, specialty=specialty)
        patient = Patient.objects.create(clinic=clinic, first_name="John", last_name="A")

        prescription = PrescriptionService.create_prescription(
            clinic=clinic, patient=patient, doctor=doctor, items=[]
        )

        self.client.login(email="doc@example.com", password="StrongPassword123!")
        self.client.get(reverse("records:prescription_print", args=[prescription.pk]))

        entry = AuditLog.objects.filter(action="print", content_type__model="prescription").latest("created_at")
        self.assertEqual(entry.object_id, prescription.pk)