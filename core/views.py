from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from clinics.profiles import DoctorProfile, SecretaryProfile
from patients.models import Patient 
from appointments.services import AppointmentService
from django.utils import timezone


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
