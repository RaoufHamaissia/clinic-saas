from datetime import timedelta

from django.utils import timezone

from .constants import (
    TRIAL_DAYS, TRIAL_PATIENT_LIMIT,
    STANDARD_MONTHLY_PRICE, STANDARD_DOCTOR_LIMIT, STANDARD_SECRETARY_LIMIT,
    PAY_PER_VISIT_PRICE,
)
from .models import Subscription, VisitRecord, Invoice


class SubscriptionService:
    @staticmethod
    def create_trial(clinic):
        return Subscription.objects.create(
            clinic=clinic,
            plan=Subscription.Plan.TRIAL,
            status=Subscription.Status.TRIALING,
            trial_ends_at=timezone.now() + timedelta(days=TRIAL_DAYS),
        )

    @staticmethod
    def get_subscription(clinic):
        return Subscription.objects.filter(clinic=clinic).first()

    @staticmethod
    def is_trial_expired(clinic):
        sub = SubscriptionService.get_subscription(clinic)
        if sub is None or sub.plan != Subscription.Plan.TRIAL:
            return False
        return sub.trial_ends_at is not None and timezone.now() > sub.trial_ends_at

    @staticmethod
    def can_add_patient(clinic):
        """Only the Trial plan caps patients — STANDARD and PAY_PER_VISIT are uncapped."""
        from patients.models import Patient

        sub = SubscriptionService.get_subscription(clinic)
        if sub is None or sub.plan != Subscription.Plan.TRIAL:
            return True

        return Patient.objects.filter(clinic=clinic).count() < TRIAL_PATIENT_LIMIT

    @staticmethod
    def can_add_doctor(clinic):
        """Only the Standard plan caps seats (1 doctor) — PAY_PER_VISIT and TRIAL are uncapped."""
        from clinics.profiles import DoctorProfile

        sub = SubscriptionService.get_subscription(clinic)
        if sub is None or sub.plan != Subscription.Plan.STANDARD:
            return True

        return DoctorProfile.objects.filter(clinic=clinic).count() < STANDARD_DOCTOR_LIMIT

    @staticmethod
    def can_add_secretary(clinic):
        """Only the Standard plan caps seats (1 secretary) — PAY_PER_VISIT and TRIAL are uncapped."""
        from clinics.profiles import SecretaryProfile

        sub = SubscriptionService.get_subscription(clinic)
        if sub is None or sub.plan != Subscription.Plan.STANDARD:
            return True

        return SecretaryProfile.objects.filter(clinic=clinic).count() < STANDARD_SECRETARY_LIMIT


class BillingService:

    @staticmethod
    def _is_billable(appointment):
        """
        A visit counts once it has genuinely happened:
        - Walk-ins count immediately (the patient is, by definition, already there).
        - Scheduled appointments count only once their status reaches DONE —
          never for cancelled/no-show, per the plan definition.
        """
        from appointments.models import Appointment

        if appointment.is_walk_in:
            return True

        return appointment.status == Appointment.Status.DONE

    @staticmethod
    def record_visit(appointment):
        """
        Idempotent: safe to call multiple times for the same appointment
        (e.g. once at walk-in creation, again if its status is later updated) —
        the OneToOneField on VisitRecord.appointment prevents double-billing.
        Only creates a record if the clinic is on the PAY_PER_VISIT plan.
        """
        sub = SubscriptionService.get_subscription(appointment.clinic)
        if sub is None or sub.plan != Subscription.Plan.PAY_PER_VISIT:
            return None

        if not BillingService._is_billable(appointment):
            return None

        record, _ = VisitRecord.objects.get_or_create(
            appointment=appointment,
            defaults={"clinic": appointment.clinic, "amount": PAY_PER_VISIT_PRICE},
        )
        return record


class InvoiceService:

    @staticmethod
    def generate_monthly_invoice(clinic, period_start, period_end):
        sub = SubscriptionService.get_subscription(clinic)
        if sub is None or sub.plan == Subscription.Plan.TRIAL:
            return None  # Trial is free — nothing to invoice.

        if sub.plan == Subscription.Plan.STANDARD:
            invoice = Invoice.objects.create(
                clinic=clinic,
                plan=Subscription.Plan.STANDARD,
                period_start=period_start,
                period_end=period_end,
                amount_due=STANDARD_MONTHLY_PRICE,
                status=Invoice.Status.DRAFT,
            )
            return invoice

        if sub.plan == Subscription.Plan.PAY_PER_VISIT:
            unbilled = VisitRecord.objects.filter(
                clinic=clinic, invoice__isnull=True,
                created_at__date__gte=period_start, created_at__date__lte=period_end,
            )

            if not unbilled.exists():
                return None  # No visits this period — no invoice generated.

            total = sum((v.amount for v in unbilled), start=type(unbilled.first().amount)(0)) #type:ignore

            invoice = Invoice.objects.create(
                clinic=clinic,
                plan=Subscription.Plan.PAY_PER_VISIT,
                period_start=period_start,
                period_end=period_end,
                amount_due=total,
                status=Invoice.Status.DRAFT,
            )

            unbilled.update(invoice=invoice)

            return invoice

        return None

    @staticmethod
    def get_for_clinic(clinic):
        return Invoice.objects.filter(clinic=clinic)