from django import forms

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