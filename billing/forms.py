from django import forms

from .models import PlanChangeRequest


class PlanChangeRequestForm(forms.ModelForm):
    class Meta:
        model = PlanChangeRequest
        fields = ["requested_plan", "payment_method", "proof_file", "reference_note"]
        widgets = {
            "requested_plan": forms.Select(attrs={"class": "form-select"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "proof_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "reference_note": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. transfer reference number (optional)"
            }),
        }