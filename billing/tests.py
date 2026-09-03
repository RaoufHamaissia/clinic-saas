# billing/tests.py
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from clinics.models import Clinic, Specialty
from clinics.profiles import DoctorProfile
from clinics.services import ClinicService, StaffService
from patients.models import Patient
from patients.services import PatientService
from appointments.models import AppointmentType
from appointments.services import AppointmentService

from .models import Subscription, VisitRecord, Invoice
from .services import SubscriptionService, BillingService, InvoiceService


class SubscriptionServiceTests(TestCase):

    def setUp(self):
        self.specialty = Specialty.objects.create(name="General Medicine")

    def test_create_clinic_starts_a_trial(self):
        clinic, doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="d@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )

        sub = SubscriptionService.get_subscription(clinic)
        self.assertEqual(sub.plan, Subscription.Plan.TRIAL) #type:ignore
        self.assertEqual(sub.status, Subscription.Status.TRIALING) #type:ignore
        self.assertIsNotNone(sub.trial_ends_at) #type:ignore

    def test_trial_patient_cap_enforced(self):
        clinic, doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="d@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )

        for i in range(50):
            PatientService.create_patient(clinic=clinic, first_name=f"P{i}", last_name="X")

        with self.assertRaises(ValueError):
            PatientService.create_patient(clinic=clinic, first_name="One Too Many", last_name="X")

    def test_standard_plan_has_no_patient_cap(self):
        clinic, doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="d@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )
        sub = SubscriptionService.get_subscription(clinic)
        sub.plan = Subscription.Plan.STANDARD #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        for i in range(55):
            PatientService.create_patient(clinic=clinic, first_name=f"P{i}", last_name="X")

        self.assertEqual(Patient.objects.filter(clinic=clinic).count(), 55)

    def test_standard_plan_caps_doctors_at_one(self):
        clinic, doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="admin@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )
        sub = SubscriptionService.get_subscription(clinic)
        sub.plan = Subscription.Plan.STANDARD #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        with self.assertRaises(ValueError):
            StaffService.create_doctor(
                clinic=clinic, email="second@example.com", password="StrongPassword123!",
                first_name="Two", last_name="Doc", specialty=self.specialty,
            )

    def test_pay_per_visit_plan_has_no_doctor_cap(self):
        clinic, doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="admin@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )
        sub = SubscriptionService.get_subscription(clinic)
        sub.plan = Subscription.Plan.PAY_PER_VISIT #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        StaffService.create_doctor(
            clinic=clinic, email="second@example.com", password="StrongPassword123!",
            first_name="Two", last_name="Doc", specialty=self.specialty,
        )

        self.assertEqual(DoctorProfile.objects.filter(clinic=clinic).count(), 2)


class BillingServiceTests(TestCase):

    def setUp(self):
        self.specialty = Specialty.objects.create(name="General Medicine")
        self.clinic, self.doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="d@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )
        sub = SubscriptionService.get_subscription(self.clinic)
        sub.plan = Subscription.Plan.PAY_PER_VISIT #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        self.patient = Patient.objects.create(clinic=self.clinic, first_name="P", last_name="X")
        self.appt_type = AppointmentType.objects.create(name="Consultation")

    def test_walk_in_is_billed_immediately(self):
        appt = AppointmentService.create_walk_in(
            clinic=self.clinic, patient=self.patient, doctor=self.doctor,
            appointment_type=self.appt_type, created_by=self.doctor.user,
        )

        self.assertTrue(VisitRecord.objects.filter(appointment=appt).exists())
        self.assertEqual(VisitRecord.objects.get(appointment=appt).amount, Decimal("50.00"))

    def test_scheduled_appointment_not_billed_until_done(self):
        appt = AppointmentService.create_appointment(
            clinic=self.clinic, patient=self.patient, doctor=self.doctor,
            appointment_type=self.appt_type, scheduled_at=timezone.now() + timedelta(days=1),
            created_by=self.doctor.user,
        )

        self.assertFalse(VisitRecord.objects.filter(appointment=appt).exists())

        AppointmentService.update_status(appointment=appt, new_status="with_doctor")
        self.assertFalse(VisitRecord.objects.filter(appointment=appt).exists())

        AppointmentService.update_status(appointment=appt, new_status="done")
        self.assertTrue(VisitRecord.objects.filter(appointment=appt).exists())

    def test_cancelled_appointment_never_billed(self):
        appt = AppointmentService.create_appointment(
            clinic=self.clinic, patient=self.patient, doctor=self.doctor,
            appointment_type=self.appt_type, scheduled_at=timezone.now() + timedelta(days=1),
            created_by=self.doctor.user,
        )

        AppointmentService.update_status(appointment=appt, new_status="cancelled")

        self.assertFalse(VisitRecord.objects.filter(appointment=appt).exists())

    def test_record_visit_is_idempotent(self):
        appt = AppointmentService.create_walk_in(
            clinic=self.clinic, patient=self.patient, doctor=self.doctor,
            appointment_type=self.appt_type, created_by=self.doctor.user,
        )

        BillingService.record_visit(appt)
        BillingService.record_visit(appt)

        self.assertEqual(VisitRecord.objects.filter(appointment=appt).count(), 1)

    def test_standard_plan_never_creates_visit_records(self):
        sub = SubscriptionService.get_subscription(self.clinic)
        sub.plan = Subscription.Plan.STANDARD #type:ignore
        sub.save() #type:ignore

        appt = AppointmentService.create_walk_in(
            clinic=self.clinic, patient=self.patient, doctor=self.doctor,
            appointment_type=self.appt_type, created_by=self.doctor.user,
        )

        self.assertFalse(VisitRecord.objects.filter(appointment=appt).exists())


class InvoiceServiceTests(TestCase):

    def setUp(self):
        self.specialty = Specialty.objects.create(name="General Medicine")
        self.clinic, self.doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="d@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )
        self.patient = Patient.objects.create(clinic=self.clinic, first_name="P", last_name="X")
        self.appt_type = AppointmentType.objects.create(name="Consultation")

    def test_trial_generates_no_invoice(self):
        invoice = InvoiceService.generate_monthly_invoice(
            self.clinic, date(2025, 1, 1), date(2025, 1, 31)
        )
        self.assertIsNone(invoice)

    def test_standard_plan_generates_flat_fee_invoice(self):
        sub = SubscriptionService.get_subscription(self.clinic)
        sub.plan = Subscription.Plan.STANDARD #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        invoice = InvoiceService.generate_monthly_invoice(
            self.clinic, date(2025, 1, 1), date(2025, 1, 31)
        )

        self.assertEqual(invoice.amount_due, Decimal("10000.00")) #type:ignore
        self.assertEqual(invoice.plan, Subscription.Plan.STANDARD) #type:ignore

    def test_pay_per_visit_invoice_sums_unbilled_visits(self):
        sub = SubscriptionService.get_subscription(self.clinic)
        sub.plan = Subscription.Plan.PAY_PER_VISIT #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        for _ in range(3):
            AppointmentService.create_walk_in(
                clinic=self.clinic, patient=self.patient, doctor=self.doctor,
                appointment_type=self.appt_type, created_by=self.doctor.user,
            )

        today = timezone.localdate()
        invoice = InvoiceService.generate_monthly_invoice(
            self.clinic, today.replace(day=1), today
        )

        self.assertEqual(invoice.amount_due, Decimal("150.00")) #type:ignore
        self.assertEqual(VisitRecord.objects.filter(invoice=invoice).count(), 3)

    def test_pay_per_visit_with_no_visits_generates_no_invoice(self):
        sub = SubscriptionService.get_subscription(self.clinic)
        sub.plan = Subscription.Plan.PAY_PER_VISIT #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        invoice = InvoiceService.generate_monthly_invoice(
            self.clinic, date(2025, 1, 1), date(2025, 1, 31)
        )

        self.assertIsNone(invoice)

    def test_visits_are_not_double_billed_across_invoice_runs(self):
        sub = SubscriptionService.get_subscription(self.clinic)
        sub.plan = Subscription.Plan.PAY_PER_VISIT #type:ignore
        sub.status = Subscription.Status.ACTIVE #type:ignore
        sub.save() #type:ignore

        AppointmentService.create_walk_in(
            clinic=self.clinic, patient=self.patient, doctor=self.doctor,
            appointment_type=self.appt_type, created_by=self.doctor.user,
        )

        today = timezone.localdate()
        first_invoice = InvoiceService.generate_monthly_invoice(self.clinic, today.replace(day=1), today)
        self.assertEqual(first_invoice.amount_due, Decimal("50.00")) #type:ignore

        # Running it again for the same period should find nothing left unbilled.
        second_invoice = InvoiceService.generate_monthly_invoice(self.clinic, today.replace(day=1), today)
        self.assertIsNone(second_invoice)


class ChargilyWebhookTests(TestCase):

    def setUp(self):
        self.specialty = Specialty.objects.create(name="General Medicine")
        self.clinic, self.doctor = ClinicService.create_clinic(
            clinic_name="Test Clinic", doctor_email="d@example.com", password="pw",
            first_name="J", last_name="D", specialty=self.specialty,
        )
        self.invoice = Invoice.objects.create(
            clinic=self.clinic, plan="standard",
            period_start=date(2025, 1, 1), period_end=date(2025, 1, 31),
            amount_due=Decimal("10000.00"), status=Invoice.Status.ISSUED,
            chargily_checkout_id="chk_test_123",
        )

    def test_webhook_rejects_invalid_signature(self):
        response = self.client.post(
            "/billing/webhook/",
            data=b'{"type": "checkout.paid", "data": {"id": "chk_test_123"}}',
            content_type="application/json",
            HTTP_SIGNATURE="not-a-real-signature",
        )
        self.assertEqual(response.status_code, 400)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.ISSUED)

    def test_webhook_marks_invoice_paid_with_valid_signature(self):
        import hmac, hashlib
        from django.conf import settings

        body = b'{"type": "checkout.paid", "data": {"id": "chk_test_123"}}'
        signature = hmac.new(settings.CHARGILY_SECRET.encode(), body, hashlib.sha256).hexdigest()

        response = self.client.post(
            "/billing/webhook/",
            data=body,
            content_type="application/json",
            HTTP_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 200)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        self.assertIsNotNone(self.invoice.paid_at)