from datetime import date
from calendar import monthrange

from django.core.management.base import BaseCommand

from billing.chargily import ChargilyService
from billing.models import Subscription
from billing.services import InvoiceService


class Command(BaseCommand):
    help = "Generates monthly invoices for all clinics on paid plans, and creates Chargily checkouts for them."

    def handle(self, *args, **options):
        today = date.today()

        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month.replace(day=1)
        last_month_end = date(last_month_end.year, last_month_end.month, 1)
        # Compute previous month's start/end
        if today.month == 1:
            period_start = date(today.year - 1, 12, 1)
        else:
            period_start = date(today.year, today.month - 1, 1)
        period_end = date(period_start.year, period_start.month, monthrange(period_start.year, period_start.month)[1])

        subscriptions = Subscription.objects.filter(
            plan__in=[Subscription.Plan.STANDARD, Subscription.Plan.PAY_PER_VISIT],
            status=Subscription.Status.ACTIVE,
        ).select_related("clinic")

        created_count = 0

        for sub in subscriptions:
            invoice = InvoiceService.generate_monthly_invoice(sub.clinic, period_start, period_end)

            if invoice is None:
                continue

            try:
                ChargilyService.create_checkout(invoice)
            except Exception as e:
                self.stderr.write(f"Failed to create Chargily checkout for invoice {invoice.pk}: {e}")
                continue

            created_count += 1
            self.stdout.write(f"Invoice #{invoice.pk} for {sub.clinic.name}: {invoice.amount_due} DA")

        self.stdout.write(self.style.SUCCESS(f"Generated {created_count} invoice(s) for {period_start} – {period_end}."))