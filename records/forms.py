from django import forms 
from django.forms import formset_factory

from clinics.profiles import DoctorProfile
from patients.models import Patient

from .models import LabworkDemand

class PrescriptionForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.none(),
        label="Patient",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.none(),
        label="Doctor",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    notes = forms.CharField(
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2})
    )

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, *kwargs)

        if clinic is not None:
            self.fields["patient"].queryset = Patient.objects.for_clinic(clinic) #type:ignore
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic)  #type:ignore


class PrescriptionItemForm(forms.Form):

    medication_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-control medication-name-input",
            "placeholder": "Medication name",
            "list": "medication-suggestions",
            "autocomplete": "off",
        })
    )
    dosage = forms.CharField(
            max_length=100, required=False,
            widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Dosage"})
        )
    frequency = forms.CharField(
            max_length=100, required=False,
            widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Frequency"})
        )
    duration = forms.CharField(
            max_length=100, required=False,
            widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Duration"})
        )
    instructions = forms.CharField(
            max_length=255, required=False,
            widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Instructions"})
        )

PrescriptionItemFormSet = formset_factory(PrescriptionItemForm, extra=3, can_delete=True)


class DoctorNoteForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.none(),
        label="Patient",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.none(),
        label="Doctor",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    content = forms.CharField(
        label="Note",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6})
    )

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)

        if clinic is not None:
            self.fields["patient"].queryset = Patient.objects.for_clinic(clinic) #type:ignore
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic) #type:ignore



class ProcedureReportForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=Patient.objects.none(), label="Patient", widget=forms.Select(attrs={"class": "form-select"}))
    doctor = forms.ModelChoiceField(queryset=DoctorProfile.objects.none(), label="Doctor", widget=forms.Select(attrs={"class": "form-select"}))
    notes = forms.CharField(required=False, label="General notes", widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)
        if clinic is not None:
            self.fields["patient"].queryset = Patient.objects.for_clinic(clinic) #type:ignore
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic) #type:ignore


class ProcedureItemForm(forms.Form):
    procedure_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Procedure name"})
    )
    findings = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Findings / notes"})
    )


ProcedureItemFormSet = formset_factory(ProcedureItemForm, extra=2, can_delete=True)


class LabworkDemandForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=Patient.objects.none(), label="Patient", widget=forms.Select(attrs={"class": "form-select"}))
    doctor = forms.ModelChoiceField(queryset=DoctorProfile.objects.none(), label="Doctor", widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)
        if clinic is not None:
            self.fields["patient"].queryset = Patient.objects.for_clinic(clinic) #type:ignore
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic) #type:ignore


class LabworkItemForm(forms.Form):
    test_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Test name"})
    )
    urgency = forms.ChoiceField(
        choices=LabworkDemand.Urgency.choices, 
        widget=forms.Select(attrs={"class": "form-select"})
    )
    clinical_indication = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Clinical indication / reason"})
    )


LabworkItemFormSet = formset_factory(LabworkItemForm, extra=2, can_delete=True)