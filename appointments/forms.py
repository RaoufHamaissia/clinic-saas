from tkinter import N

from django import forms

from clinics.profiles import DoctorProfile
from patients.models import Patient

class AppointmentForm(forms.Form):
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

    scheduled_at = forms.DateTimeField(
        label="Date & Time",
        widget=forms.DateTimeInput(
            attrs={"class": "form-control", "type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)

        if clinic is not None:
            self.fields["patient"].queryset = Patient.objects.for_clinic(clinic)  #type:ignore
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic)  #type:ignore