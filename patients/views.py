from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import PatientForm
from .services import PatientService


# Create your views here.

@login_required
def patient_list(request):
    clinic = request.user.clinic

    patients = PatientService.get_for_clinic(clinic)

    context = {"patients": patients}
    return render(request, "patients/list.html", context)