from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from clinics.profiles import DoctorProfile, SecretaryProfile
from patients.models import Patient 
from appointments.services import AppointmentService
from django.utils import timezone

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

from .services import AuditLogService


# Create your views here.

@login_required
def dashboard(request):

    clinic = request.user.clinic

    doctors_count = DoctorProfile.objects.filter(clinic=clinic).count()
    secretaries_count = SecretaryProfile.objects.filter(clinic=clinic).count()
    patients_count = Patient.objects.filter(clinic=clinic).count() if clinic else 0

    todays_appointments = (
        AppointmentService.get_for_day(clinic, timezone.localdate())
        if clinic else []
    )

    context = {
        "clinic": clinic,
        "doctors_count": doctors_count,
        "secretaries_count": secretaries_count,
        "patients_count": patients_count,
        "todays_appointments": todays_appointments,
        "todays_appointments_count": len(todays_appointments) if clinic else 0,

    }

    return render(request, 'core/dashboard.html', context )


@login_required
def audit_log_view(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only a platform superuser can view the audit log.")

    filters = {
        "action": request.GET.get("action", ""),
        "actor_email": request.GET.get("actor_email", ""),
        "start_date": request.GET.get("start_date", ""),
        "end_date": request.GET.get("end_date", ""),
    }

    logs = AuditLogService.get_all(filters)

    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "page_obj": page_obj,
        "filters": filters,
        "action_choices": AuditLogService.Action.choices,
    }
    return render(request, "core/audit_log.html", context)