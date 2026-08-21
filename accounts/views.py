from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import LoginForm

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