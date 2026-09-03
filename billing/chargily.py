import hashlib
import hmac

import requests
from django.conf import settings

class ChargilyService:

    @staticmethod
    def create_checkout(invoice):
        """
        Creates a Chargily Pay checkout session for the given invoice's
        amount, in sandbox/test mode (settings.CHARGILY_BASE_URL points at
        pay.chargily.net/test/... until you switch to live credentials).
        """
        response = requests.post(
            f"{settings.CHARGILY_BASE_URL}checkouts",
            headers={
                "Authorization": f"Bearer {settings.CHARGILY_SECRET}",
                "Content-Type": "application/json",
            },
            json={
                "amount": float(invoice.amount_due),
                "currency": "dzd",
                "success_url": settings.CHARGILY_SUCCESS_URL,
                "failure_url": settings.CHARGILY_FAILURE_URL,
                "webhook_endpoint": settings.CHARGILY_WEBHOOK_URL,
                "description": f"MediCore invoice #{invoice.pk} — {invoice.clinic.name}",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        invoice.chargily_checkout_id = data["id"]
        invoice.chargily_checkout_url = data["checkout_url"]
        invoice.status = invoice.__class__.Status.ISSUED
        invoice.save(update_fields=["chargily_checkout_id", "chargily_checkout_url", "status"])

        return invoice


    @staticmethod
    def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
        """
        HMAC-SHA256 of the raw request body, keyed with the Chargily secret,
        compared against the 'signature' header — following the pattern used
        by Chargily's own JS/Python SDKs.

        IMPORTANT: verify this exact scheme against Chargily's dashboard/API
        reference before relying on it in production — this was reconstructed
        from their SDK repos, not confirmed against their canonical spec page.
        """
        if not signature_header:
            return False

        expected = hmac.new(
            settings.CHARGILY_SECRET.encode(), raw_body, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature_header)


    @staticmethod
    def handle_webhook_event(event: dict):
        """
        Processes a verified Chargily webhook payload. Expects something
        like {"type": "checkout.paid", "data": {"id": "<checkout_id>", ...}}.
        Marks the matching Invoice as paid, idempotently.
        """
        from django.utils import timezone
        from .models import Invoice

        event_type = event.get("type", "")
        checkout_id = event.get("data", {}).get("id")

        if not checkout_id:
            return None

        if event_type == "checkout.paid":
            invoice = Invoice.objects.filter(chargily_checkout_id=checkout_id).first()
            if invoice and invoice.status != Invoice.Status.PAID:
                invoice.status = Invoice.Status.PAID
                invoice.paid_at = timezone.now()
                invoice.save(update_fields=["status", "paid_at"])
            return invoice

        if event_type in ("checkout.failed", "checkout.expired"):
            invoice = Invoice.objects.filter(chargily_checkout_id=checkout_id).first()
            if invoice and invoice.status == Invoice.Status.ISSUED:
                invoice.status = Invoice.Status.OVERDUE
                invoice.save(update_fields=["status"])
            return invoice

        return None