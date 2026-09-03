from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required

from django.contrib.auth.forms import PasswordChangeForm

from .forms import LoginForm, ProfileForm


# Create your views here.

def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, email=email, password=password)

            if user is not None:
                if not user.is_active:
                    form.add_error(None, "Your account is inactive.")

                else:   
                    login(request, user)

                    next_url = request.GET.get("next") 

                    if next_url:
                        return redirect(next_url)

                    return redirect('core:dashboard')

            else:
                form.add_error(None, 'Invalid email or password.')

    else:
        form = LoginForm()

    context = { "form": form}
    return render(request, 'accounts/login.html', context) 


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)

        messages.success(request, "You have been logged out successfully")

        return redirect("accounts:login")
    
    return redirect("core:dashboard")


@login_required
def edit_profile(request):
    if request.method == "POST":
        if "update_profile" in request.POST:
            profile_form = ProfileForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully")
                return redirect("accounts:edit_profile")

        elif "change_password" in request.POST:
            profile_form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # keeps the user logged in after password change
                messages.success(request, "Password changed successfully")
                return redirect("accounts:edit_profile")

        else:
            profile_form = ProfileForm(instance=request.user)
            password_form = PasswordChangeForm(request.user)

    else:
        profile_form = ProfileForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    context = {"profile_form": profile_form, "password_form": password_form}
    return render(request, "accounts/edit_profile.html", context)