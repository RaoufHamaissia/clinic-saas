from django import forms

from .models import Specialty
from accounts.models import User

from django.contrib.auth.password_validation import validate_password

from .services import SpecialtyService




class ClinicRegistrationForm(forms.Form):
    #-------------------
    # Clinic information
    #-------------------
    clinic_name = forms.CharField(max_length=200, label="Clinic name",
                                  widget=forms.TelInput(
                                      attrs={
                                          "class": "form-control",
                                          "placeholder": "Enter clinic name",
                                      }
                                  )
                                )

    clinic_phone = forms.CharField(max_length=50, required=False, label="Phone number",
                                   widget=forms.TelInput(
                                       attrs={
                                           "class": "form-control",
                                           "placeholder": "Enter clinic phone number"
                                       }
                                   )
                                )
    clinic_address = forms.CharField(required=False, label="Address", 
                                     widget=forms.Textarea(
                                         attrs={
                                             "class": "form-control",
                                             "rows": 3,
                                             "placeholder": "Enter clinic address"
                                         }
                                     )
                                    )
    #-------------------
    # Doctor account
    #-------------------
    first_name = forms.CharField(max_length=150, label="First name",
                                 widget=forms.TelInput(
                                     attrs={
                                        "class": "form-control",
                                        "placeholder": "First name",
                                     }
                                 )
                                )

    last_name = forms.CharField(max_length=150, label="Last name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Last name",
            }
        )
    )

    email = forms.EmailField(label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "doctor@example.com",
            }
        )
    )

    password = forms.CharField(label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create a password",
            }
        )
    )

    password_confirm = forms.CharField(label="Confirm password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your password",
            }
        )
    )   

    specialty = forms.CharField(
        max_length=150,
        label="Specialty",        
        widget=forms.TextInput(
            attrs={
                "class": "form-control specialty-input",
                "placeholder": "Start typing e.g. Cardiology",
                "list": "specialty-suggestions",
                "autocomplete": "off",
            }
        )
    )

    #-------------------
    # Validation
    #-------------------

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email

    def clean_specialty(self):
        name = self.cleaned_data["specialty"].strip()

        if not name:
            raise forms.ValidationError("Specialty is required.")

        return SpecialtyService.get_or_create(name)

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password") #type:ignore
        password_confirm = cleaned_data.get("password_confirm") #type:ignore

        if password and password_confirm:
            if password != password_confirm:
                self.add_error(
                    "password_confirm",
                    "Passwords do not match."
                )

        if password:
            try:
                validate_password(password=password)
            except forms.ValidationError as error:
                self.add_error("password", error)


        return cleaned_data
        
        
