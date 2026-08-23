from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

import appointments

from .forms import AppointmentForm, WalkInForm
from .services import AppointmentService
from .models import Appointment

# Create your views here.

def _require_clinic(request):
    clinic = request.user.clinic

    if clinic is None:
        raise PermissionDenied("You must belong to a clinic to manage appointments.")

    return clinic

@login_required
def day_view(request, date=None):
    clinic = _require_clinic(request)

    day = parse_date(date) if date else None
    if day is None:
        day = timezone.localdate()

    appointments = AppointmentService.get_for_day(clinic, day)

    context = {
        "appointments": appointments,
        "day": day
    }

    return render(request, "appointments/day_list.html", context)


@login_required
def add_appointment(request):
    clinic = _require_clinic(request)

    if request.method == "POST":
        form = AppointmentForm(request.POST, clinic=clinic)

        if form.is_valid():
            AppointmentService.create_appointment(
                clinic=clinic,
                patient=form.cleaned_data['patient'],
                doctor=form.cleaned_data['doctor'],
                scheduled_at=form.cleaned_data['scheduled_at'],
                created_by=request.user,
            )

            messages.success(request, "Appointment booked successfully")

            return redirect("appointment:day")

    else:
        form = AppointmentForm(clinic=clinic)

    context = {"form": form}
    return render(request, "appointments/add.html", context)


@login_required
def add_walk_in(request):
    clinic = _require_clinic(request)

    if request.method == 'POST':
        form = WalkInForm(request.POST, clinic=clinic)

        if form.is_valid():
            AppointmentService.create_walk_in(
                clinic=clinic,
                patient=form.cleaned_data['patient'],
                doctor=form.cleaned_data['doctor'],
                created_by=request.user,
            )

            messages.success(request, "Walk-in added to today's list")

            return redirect("appointments:day")

    else: 
        form = WalkInForm(clinic=clinic)

    context = {"form": form}
    return render(request, "appointments/walk_in.html", context)


@login_required
@require_POST
def update_status(request, pk):
    clinic = _require_clinic(request)

    appointment = get_object_or_404(Appointment.objects.for_clinic(clinic, pk=pk)) #type:ignore

    new_status = request.POST.get("status")

    try:
        AppointmentService.update_status(appointment=appointment, new_status=new_status)
    except ValueError:
        messages.error(request, "Invalid status.")
    else:
        messages.success(request, "Status updated")

    return redirect("appointments:day")