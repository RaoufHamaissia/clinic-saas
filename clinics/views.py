from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login
from django.db import IntegrityError
from django.shortcuts import redirect
from django.http import JsonResponse

from .forms import ClinicRegistrationForm
from .services import ClinicService, SpecialtyService

# Create your views here.

def register_clinic(request):
    if request.method == "POST":
        form = ClinicRegistrationForm(request.POST)

        if form.is_valid():
            try:
                clinic, doctor = ClinicService.create_clinic(
                    clinic_name=form.cleaned_data["clinic_name"],
                    clinic_phone=form.cleaned_data["clinic_phone"],
                    clinic_address=form.cleaned_data["clinic_address"],
                    doctor_email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    specialty=form.cleaned_data["specialty"],
                )
            except IntegrityError:
                form.add_error("email", "An account with this email already exist.")

            else:
                login(request, doctor.user)

                messages.success(request, "Your clinic has been created successfully")

                return redirect("core:dashboard")

    else:
        form = ClinicRegistrationForm()

    context = {"form": form}
    return render(request, "clinics/register.html", context)


def specialty_suggest(request):
    """
    Deliberately no @login_required — this powers autocomplete on the
    public clinic registration page, where nobody is authenticated yet.
    """
    query = request.GET.get("q", "")
    specialties = SpecialtyService.suggest(query)

    return JsonResponse({"results": [s.name for s in specialties]})