from django import forms

from phonenumber_field.formfields import PhoneNumberField

from .models import User


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email",
                             widget=forms.EmailInput(
                                 attrs={
                                     "class": "form-control",
                                     "placeholder": "Enter your email",
                                     "autocomplete": "email",
                                 }
                             ))

    password = forms.CharField(label="Password",
                               widget=forms.PasswordInput(
                                   attrs={
                                        "class": "form-control",
                                        "placeholder": "Enter your password",
                                        "autocomplete": "current-password",
                                   }
                               ))



class ProfileForm(forms.ModelForm):
    phone = PhoneNumberField(
        required=False,
        label="Phone",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+213 555 12 34 56"})
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("An account with this email already exists.")

        return email