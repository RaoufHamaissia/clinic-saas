from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from appointments.services import AppointmentService
from records.services import (
    PrescriptionService, DoctorNoteService, ProcedureReportService, LabworkDemandService,
)
from records.forms import (
    PrescriptionForm, PrescriptionItemFormSet, DoctorNoteForm,
    ProcedureReportForm, ProcedureItemFormSet,
    LabworkDemandForm, LabworkItemFormSet,
)
from .forms import PatientForm
from .services import PatientService
from .models import Patient


# Create your views here.

def _require_clinic(request):
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
    clinic = _require_clinic(request)

    patients = PatientService.get_for_clinic(clinic)

    context = {"patients": patients}
    return render(request, "patients/list.html", context)

@login_required
def add_patient(request):
    clinic = _require_clinic(request)

    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            try:
                PatientService.create_patient(
                    clinic=clinic,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    date_of_birth=form.cleaned_data["date_of_birth"],
                    approximate_age=form.cleaned_data["approximate_age"],
                    phone=form.cleaned_data["phone"],
                    address=form.cleaned_data["address"],
                    reason_for_visit=form.cleaned_data["reason_for_visit"],
                )
            except ValueError as e:
                form.add_error(None, str(e))
            else:
                messages.success(request, "Patient added successfully")
                return redirect("patients:list")

    else:
        form = PatientForm()

    context = {"form": form}
    return render(request, "patients/add.html", context)
def _get_patient_or_404(clinic, patient_id):
    return get_object_or_404(Patient.objects.for_clinic(clinic), pk=patient_id) #type:ignore

@login_required
def patient_detail(request, pk):
    clinic = _require_clinic(request)

    patient = _get_patient_or_404(clinic, pk)

    filters = {
        prefix: {
            "search": request.GET.get(f"{prefix}_search", ""),
            "start": request.GET.get(f"{prefix}_start", ""),
            "end": request.GET.get(f"{prefix}_end", ""),
        }
        for prefix in ("appt", "rx", "note", "proc", "lab")
    }

    context = {
        "patient": patient,
        "appointments": AppointmentService.get_for_patient(
            clinic, patient,
            search=filters["appt"]["search"] or None,
            start_date=filters["appt"]["start"] or None,
            end_date=filters["appt"]["end"] or None,
        ),
        "prescriptions": PrescriptionService.get_for_patient(
            clinic, patient,
            search=filters["rx"]["search"] or None,
            start_date=filters["rx"]["start"] or None,
            end_date=filters["rx"]["end"] or None,
        ),
        "notes": DoctorNoteService.get_for_patient(
            clinic, patient,
            search=filters["note"]["search"] or None,
            start_date=filters["note"]["start"] or None,
            end_date=filters["note"]["end"] or None,
        ),
        "procedure_reports": ProcedureReportService.get_for_patient(
            clinic, patient,
            search=filters["proc"]["search"] or None,
            start_date=filters["proc"]["start"] or None,
            end_date=filters["proc"]["end"] or None,
        ),
        "labwork_demands": LabworkDemandService.get_for_patient(
            clinic, patient,
            search=filters["lab"]["search"] or None,
            start_date=filters["lab"]["start"] or None,
            end_date=filters["lab"]["end"] or None,
        ),
        "filters": filters,
    }
    return render(request, "patients/detail.html", context)

@login_required
def add_prescription(request, patient_id):
    clinic = _require_clinic(request)
    patient = _get_patient_or_404(clinic, patient_id)

    if request.method == "POST":
        form = PrescriptionForm(request.POST, clinic=clinic)
        formset = PrescriptionItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            items = [
                {
                    "medication_name": f.cleaned_data["medication_name"],
                    "dosage": f.cleaned_data["dosage"],
                    "frequency": f.cleaned_data["frequency"],
                    "duration": f.cleaned_data["duration"],
                    "instructions": f.cleaned_data["instructions"],
                }
                for f in formset
                if f.cleaned_data and not f.cleaned_data.get("DELETE") and f.cleaned_data.get("medication_name")
            ]

            prescription = PrescriptionService.create_prescription(
                clinic=clinic, patient=patient, doctor=form.cleaned_data["doctor"],
                notes=form.cleaned_data["notes"], items=items,
            )

            messages.success(request, "Prescription created")
            return redirect("records:prescription_print", pk=prescription.pk)

    else:
        form = PrescriptionForm(clinic=clinic)
        formset = PrescriptionItemFormSet()

    context = {"form": form, "formset": formset, "patient": patient}
    return render(request, "records/prescription_add.html", context)


@login_required
def add_note(request, patient_id):
    clinic = _require_clinic(request)
    patient = _get_patient_or_404(clinic, patient_id)

    if request.method == "POST":
        form = DoctorNoteForm(request.POST, clinic=clinic)

        if form.is_valid():
            note = DoctorNoteService.create_note(
                clinic=clinic, patient=patient, doctor=form.cleaned_data["doctor"],
                content=form.cleaned_data["content"],
            )

            messages.success(request, "Note saved")
            return redirect("records:note_print", pk=note.pk)

    else:
        form = DoctorNoteForm(clinic=clinic)

    context = {"form": form, "patient": patient}
    return render(request, "records/note_add.html", context)


@login_required
def add_procedure_report(request, patient_id):
    clinic = _require_clinic(request)
    patient = _get_patient_or_404(clinic, patient_id)

    if request.method == "POST":
        form = ProcedureReportForm(request.POST, clinic=clinic)
        formset = ProcedureItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            items = [
                {"procedure_name": f.cleaned_data["procedure_name"], "findings": f.cleaned_data.get("findings", "")}
                for f in formset
                if f.cleaned_data and not f.cleaned_data.get("DELETE") and f.cleaned_data.get("procedure_name")
            ]

            report = ProcedureReportService.create_report(
                clinic=clinic, patient=patient, doctor=form.cleaned_data["doctor"],
                notes=form.cleaned_data["notes"], items=items,
            )

            messages.success(request, "Procedure report created")
            return redirect("records:procedure_report_print", pk=report.pk)

    else:
        form = ProcedureReportForm(clinic=clinic)
        formset = ProcedureItemFormSet()

    context = {"form": form, "formset": formset, "patient": patient}
    return render(request, "records/procedure_report_add.html", context)


@login_required
def add_labwork_demand(request, patient_id):
    clinic = _require_clinic(request)
    patient = _get_patient_or_404(clinic, patient_id)

    if request.method == "POST":
        form = LabworkDemandForm(request.POST, clinic=clinic)
        formset = LabworkItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            items = [
                {
                    "test_name": f.cleaned_data["test_name"],
                    "urgency": f.cleaned_data["urgency"],
                    "clinical_indication": f.cleaned_data.get("clinical_indication", ""),
                }
                for f in formset
                if f.cleaned_data and not f.cleaned_data.get("DELETE") and f.cleaned_data.get("test_name")
            ]

            demand = LabworkDemandService.create_demand(
                clinic=clinic, patient=patient, doctor=form.cleaned_data["doctor"], items=items,
            )

            messages.success(request, "Labwork demand created")
            return redirect("records:labwork_demand_print", pk=demand.pk)

    else:
        form = LabworkDemandForm(clinic=clinic)
        formset = LabworkItemFormSet()

    context = {"form": form, "formset": formset, "patient": patient}
    return render(request, "records/labwork_demand_add.html", context)