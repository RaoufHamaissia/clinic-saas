from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .forms import PatientForm
from .services import PatientService


# Create your views here.

def _required_clinic(request):
    """
    Guards against users with no clinic (e.g.) platform superusers with no clinic assigned
    hitting patient views. Returns the clinic or raises.
    """
    clinic = request.user.clinic

    if clinic is None:
        raise PermissionDenied("you must belong to a clinic to manage patients.")

    return clinic


@login_required
def patient_list(request):
    clinic = _required_clinic(request)

    patients = PatientService.get_for_clinic(clinic)

    context = {"patients": patients}
    return render(request, "patients/list.html", context)

@login_required
def add_patient(request):
    clinic = _required_clinic(request)

    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            PatientService.create_patient(
                clinic=clinic,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                date_of_birth=form.cleaned_data['date_of_birth'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                reason_for_visit=form.cleaned_data['reason_for_visit'],
            )

            messages.success(request, "Patient added successfully")

            return redirect("patients:list")
        
    else:
        form = PatientForm()

    context = {"form": form}
    return render(request, "patients/add.html", context)