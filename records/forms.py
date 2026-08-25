from django import forms 
from django.forms import formset_factory

from clinics.profiles import DoctorProfile
from patients.models import Patient

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
