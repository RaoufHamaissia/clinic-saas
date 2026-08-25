from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string

from .forms import PrescriptionForm, PrescriptionItemFormSet, DoctorNoteForm
from .services import PrescriptionService, MedicationService, DoctorNoteService
from .models import Prescription, DoctorNote

from django.http import JsonResponse


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