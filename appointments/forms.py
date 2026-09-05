from django import forms
from django.utils import timezone
from django.utils.timezone import is_naive

from clinics.profiles import DoctorProfile
from patients.models import Patient

from .services import AppointmentTypeService

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

    type = forms.CharField(
        max_length=150,
        label="Appointment type",
        widget=forms.TextInput(attrs={
            "class": "form-control appointment-type-input",
            "placeholder": "e.g. Colonoscopy",
            "list": "appointment-type-suggestions",
            "autocomplete": "off",
        })
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
            self.fields["patient"].queryset = Patient.objects.for_clinic(clinic) #type:ignore
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic) #type:ignore

    def clean_type(self):
        name = self.cleaned_data["type"].strip()

        if not name:
            raise forms.ValidationError("Appointment type is required.")

        return AppointmentTypeService.get_or_create(name)

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data["scheduled_at"]

        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at)

        if scheduled_at < timezone.now():
            raise forms.ValidationError("You can't book an appointment in the past.")

        return scheduled_at

class WalkInForm(forms.Form):
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

    type = forms.CharField(
        max_length=150,
        label="Appointment type",
        widget=forms.TextInput(attrs={
            "class": "form-control appointment-type-input",
            "placeholder": "e.g. Colonoscopy",
            "list": "appointment-type-suggestions",
            "autocomplete": "off",
        })
    )

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)

        if clinic is not None:
            self.fields["patient"].queryset = Patient.objects.for_clinic(clinic) #type:ignore
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic) #type:ignore

    def clean_type(self):
        name = self.cleaned_data["type"].strip()

        if not name:
            raise forms.ValidationError("Appointment type is required.")

        return AppointmentTypeService.get_or_create(name)


class AppointmentEditForm(forms.Form):
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.none(),
        label="Doctor",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    type = forms.CharField(
        max_length=150,
        label="Appointment type",
        widget=forms.TextInput(attrs={
            "class": "form-control appointment-type-input",
            "placeholder": "e.g. Colonoscopy",
            "list": "appointment-type-suggestions",
            "autocomplete": "off",
        })
    )

    scheduled_at = forms.DateTimeField(
        required=False,
        label="Date & time",
        widget=forms.DateTimeInput(
            attrs={"class": "form-control", "type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    def __init__(self, *args, clinic=None, **kwargs):
        super().__init__(*args, **kwargs)

        if clinic is not None:
            self.fields["doctor"].queryset = DoctorProfile.objects.filter(clinic=clinic) #type:ignore

    def clean_type(self):
        name = self.cleaned_data["type"].strip()

        if not name:
            raise forms.ValidationError("Appointment type is required.")

        return AppointmentTypeService.get_or_create(name)


