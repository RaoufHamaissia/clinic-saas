from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string

from .forms import (
    PrescriptionForm, PrescriptionItemFormSet, DoctorNoteForm,
    ProcedureReportForm, ProcedureItemFormSet,
    LabworkDemandForm, LabworkItemFormSet,
    DoctorDocumentProfileForm,
)

from .services import (
    PrescriptionService, MedicationService, DoctorNoteService,
    ProcedureReportService, LabworkDemandService,
)
from .models import DoctorDocumentProfile, Prescription, DoctorNote, ProcedureReport, LabworkDemand

from django.http import JsonResponse

from accounts.models import User


# Create your views here.

@login_required
def medication_suggest(request):
    query = request.GET.get("q", "")
    medications = MedicationService.suggest(query)

    return JsonResponse({"results": [m.name for m in medications]})

def _require_clinic(request):
    clinic = request.user.clinic

    if clinic is None:
        raise PermissionDenied("You must belong to a clinic to manage medical records.")

    return clinic

@login_required
def prescription_list(request):
    clinic = _require_clinic(request)

    prescriptions = PrescriptionService.get_for_clinic(clinic)

    context = {"prescriptions": prescriptions}
    return render(request, "records/prescription,_list.html")


@login_required
def add_prescription(request):
    clinic = _require_clinic(request)

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
                clinic=clinic,
                patient=form.cleaned_data["patient"],
                doctor=form.cleaned_data["doctor"],
                notes=form.cleaned_data["notes"],
                items=items,
                
            )

            messages.success(request, "Prescription created")

            return redirect("records:prescription_print", pk=prescription.pk)

    else:
        form = PrescriptionForm(clinic=clinic)
        formset = PrescriptionItemFormSet()

    context = {"form": form, "formset": formset}
    return render(request, "records/prescription_add.html", context)

@login_required
def prescription_print(request, pk):
    clinic = _require_clinic(request)

    prescription = get_object_or_404(
        Prescription.objects.for_clinic(clinic).select_related("patient", "doctor__user", "clinic"), #type:ignore
        pk=pk,
    )

    html_string = render_to_string("records/prescription_pdf.html", {
        "prescription": prescription,
        "clinic": clinic,
        "doctor": prescription.doctor,
        "items": prescription.items.all()

    })

    from weasyprint import HTML

    pdf_bytes = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="prescription_{prescription.pk}.pdf'

    return response




@login_required
def note_list(request):
    clinic = _require_clinic(request)

    notes = DoctorNoteService.get_for_clinic(clinic)

    context = {"notes": notes}
    return render(request, "records/note_list.html", context)

@login_required
def add_note(request):
    clinic = _require_clinic(request)

    if request.method == "POST":
        form = DoctorNoteForm(request.POST, clinic=clinic)

        if form.is_valid():
            note = DoctorNoteService.create_note(
                clinic=clinic,
                patient=form.cleaned_data["patient"],
                doctor=form.cleaned_data["doctor"],
                content=form.cleaned_data["content"],
            )

            messages.success(request, "Note saved")

            return redirect("records:note_print", pk=note.pk)

    else:
        form = DoctorNoteForm(clinic=clinic)

    context = {"form": form}
    return render(request, "records/note_add.html", context)


@login_required
def note_print(request, pk):
    clinic = _require_clinic(request)

    note = get_object_or_404(
        DoctorNote.objects.for_clinic(clinic).select_related("patient", "doctor__user", "clinic"), #type:ignore
        pk=pk,
    )

    html_string = render_to_string("records/note_pdf.html", {
        "note": note,
        "clinic": clinic,
        "doctor": note.doctor,
    })

    from weasyprint import HTML

    pdf_bytes = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="note_{note.pk}.pdf"'
    return response





@login_required
def procedure_report_list(request):
    clinic = _require_clinic(request)
    reports = ProcedureReportService.get_for_clinic(clinic)
    return render(request, "records/procedure_report_list.html", {"reports": reports})

@login_required
def add_procedure_report(request):
    clinic = _require_clinic(request)

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
                clinic=clinic,
                patient=form.cleaned_data["patient"],
                doctor=form.cleaned_data["doctor"],
                notes=form.cleaned_data["notes"],
                items=items,
            )

            messages.success(request, "Procedure report created")
            return redirect("records:procedure_report_print", pk=report.pk)

    else:
        form = ProcedureReportForm(clinic=clinic)
        formset = ProcedureItemFormSet()

    return render(request, "records/procedure_report_add.html", {"form": form, "formset": formset})


@login_required
def procedure_report_print(request, pk):
    clinic = _require_clinic(request)

    report = get_object_or_404(
        ProcedureReport.objects.for_clinic(clinic).select_related("patient", "doctor__user", "clinic"), #type:ignore
        pk=pk,
    ) 

    html_string = render_to_string("records/procedure_report_pdf.html", {
        "report": report, "clinic": clinic, "doctor": report.doctor, "items": report.items.all(),
    })

    from weasyprint import HTML
    pdf_bytes = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="procedure_report_{report.pk}.pdf"'
    return response



@login_required
def labwork_demand_list(request):
    clinic = _require_clinic(request)
    demands = LabworkDemandService.get_for_clinic(clinic)
    return render(request, "records/labwork_demand_list.html", {"demands": demands})


@login_required
def add_labwork_demand(request):
    clinic = _require_clinic(request)

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
                clinic=clinic,
                patient=form.cleaned_data["patient"],
                doctor=form.cleaned_data["doctor"],
                items=items,
            )

            messages.success(request, "Labwork demand created")
            return redirect("records:labwork_demand_print", pk=demand.pk)

    else:
        form = LabworkDemandForm(clinic=clinic)
        formset = LabworkItemFormSet()

    return render(request, "records/labwork_demand_add.html", {"form": form, "formset": formset})


@login_required
def labwork_demand_print(request, pk):
    clinic = _require_clinic(request)

    demand = get_object_or_404(
        LabworkDemand.objects.for_clinic(clinic).select_related("patient", "doctor__user", "clinic"), #type:ignore
        pk=pk,
    )

    html_string = render_to_string("records/labwork_demand_pdf.html", {
        "demand": demand, "clinic": clinic, "doctor": demand.doctor, "items": demand.items.all(),
    })

    from weasyprint import HTML
    pdf_bytes = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="labwork_demand_{demand.pk}.pdf"'
    return response


@login_required
def edit_document_profile(request):
    if request.user.role != User.Role.DOCTOR:
        raise PermissionDenied("Only doctors have a document profile.")

    doctor = getattr(request.user, "doctor_profile", None)
    if doctor is None:
        raise PermissionDenied("Your account has no doctor profile.")

    document_profile, _ = DoctorDocumentProfile.objects.get_or_create(doctor=doctor)

    if request.method == "POST":
        form = DoctorDocumentProfileForm(request.POST, request.FILES, instance=document_profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Document profile updated")
            return redirect("records:edit_document_profile")

    else: 
        form = DoctorDocumentProfileForm(instance=document_profile) 

    context = {"form": form}
    return render(request, "records/document_profile.html", context)