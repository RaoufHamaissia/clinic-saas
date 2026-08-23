from django.contrib import admin

from .models import Appointment

# Register your models here.

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "clinic",
        "scheduled_at",
        "status",
        "is_walk_in",
    )

    list_filter = (
        "clinic",
        "status",
        "is_walk_in",
        "doctor",
    )

    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "doctor__user__email"
    )