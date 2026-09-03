from django.db import models

# Create your models here.

class Subscription(models.Model):
    class Plan(models.TextChoices):
        TRIAL = "trial", "Trial"
        STANDARD = "standard", "Standard (1 doctor, 1 secretary)"
        PAY_PER_VISIT = "pay_per_visit", "Pay per visit"

    class Status(models.TextChoices):
        TRIALING = "trialing", "Trialing"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    clinic = models.OneToOneField("clinics.Clinic", on_delete=models.CASCADE, related_name="subscription")


    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.TRIAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)

    trial_ends_at = models.DateTimeField(null=True, blank=True)

    # For STANDARD's flat monthly billing cycle. Unused for PAY_PER_VISIT
    # (which bills retroactively based on VisitRecords) and TRIAL (free).
    current_period_start = models.DateField(null=True, blank=True)
    current_period_end = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.clinic} — {self.get_plan_display()} ({self.get_status_display()})" #type:ignore


class VisitRecord(models.Model):
    """
    One billable event per Appointment, for clinics on the PAY_PER_VISIT
    plan. The OneToOneField on `appointment` guarantees exactly one charge
    per appointment regardless of how many times its status changes.
    """
    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT, related_name="visit_records")
    appointment = models.OneToOneField(
        "appointments.Appointment", on_delete=models.PROTECT, related_name="visit_record"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    invoice = models.ForeignKey(
        "billing.Invoice", null=True, blank=True, on_delete=models.SET_NULL, related_name="visit_records"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Visit — {self.clinic} — {self.amount} DA"


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    clinic = models.ForeignKey("clinics.Clinic", on_delete=models.PROTECT, related_name="invoices")

    plan = models.CharField(max_length=20, choices=Subscription.Plan.choices)
    period_start = models.DateField()
    period_end = models.DateField()

    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    chargily_checkout_id = models.CharField(max_length=100, blank=True)
    chargily_checkout_url = models.URLField(blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start"]

    def __str__(self):
        return f"Invoice {self.pk} — {self.clinic} — {self.amount_due} DA ({self.get_status_display()})" #type:ignore