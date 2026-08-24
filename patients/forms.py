from logging import PlaceHolder
from turtle import textinput

from django import forms
from django.forms.widgets import TextInput
from phonenumber_field.formfields import PhoneNumberField

class PatientForm(forms.Form):
    first_name = forms.CharField( #type:ignore
        max_length=150,
        label="First name",
        widget=forms.TextInput(
                         attrs={
                               "class": "form-control",
                                "placeholder": "First name",
                                }
                            )
    )
    
    last_name = forms.CharField(
        max_length=150,
        label="Last name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last name",
            }
        )
    )

    date_of_birth = forms.DateField(
        required=False,
        label="Date of birth",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        )
    )

    approximate_age = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=130,
        label="Approximate age (if DOB unknown)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. 45",
            }
        )
    )

    phone = PhoneNumberField(  #type:ignore
        required=False,
        label="Phone",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "+213 555 12 34 56",
            }
        )
    )

    address = forms.CharField(
        required=False,
        label="Address",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Enter patient address",
            }
        )
    )

    reason_for_visit = forms.CharField(
        required=False,
        max_length=255,
        label="Reason for visit",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. follow-up, chest pain, prescription renewal",
            }
        )
    )