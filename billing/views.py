from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .chargily import ChargilyService
from .models import Invoice
from .services import SubscriptionService, InvoiceService


# Create your views here.


def _require_clinic_admin(request):
    clinic = request.user.clinic

    if clinic is None or not request.user.is_clinic_admin:
        raise PermissionDenied("Only a clinic administrator can view billing.")

    return clinic

@login_required
def subscription_status(request):
    clinic = _require_clinic_admin(request)

    subscription = SubscriptionService.get_subscription(clinic)
    invoices = InvoiceService.get_for_clinic(clinic)
    trial_expired = SubscriptionService.is_trial_expired(clinic)

    context = {
        "subscription": subscription,
        "invoices": invoices,
        "trial_expired": trial_expired,
    }
    return render(request, "billing/subscription.html", context)

@login_required
def pay_invoice(request, pk):
    clinic = _require_clinic_admin(request)

    invoice = get_object_or_404(Invoice, pk=pk, clinic=clinic)

    if not invoice.chargily_checkout_url:
        ChargilyService.create_checkout(invoice)
        invoice.refresh_from_db()

    return redirect(invoice.chargily_checkout_url)


def payment_success(request):
    return render(request, "billing/payment_success.html")


def payment_failure(request):
    return render(request, "billing/payment_failure.html")


@csrf_exempt
@require_POST
def chargily_webhook(request):
    signature = request.META.get("HTTP_SIGNATURE", "")

    if not ChargilyService.verify_webhook_signature(request.body, signature):
        return HttpResponseBadRequest("Invalid signature")

    import json
    try:
        event = json.loads(request.body)
    except ValueError:
        return HttpResponseBadRequest("Invalid JSON")

    ChargilyService.handle_webhook_event(event)

    return HttpResponse(status=200)