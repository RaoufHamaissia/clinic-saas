from django.contrib import admin
from .models import DoctorDocumentProfile, Prescription, PrescriptionItem, Medication


# Register your models here.

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "clinic", "created_at")
    list_filter = ("clinic", "doctor")
    search_fields = ("patient__first_name", "patient__last_name")
    inlines = [PrescriptionItemInline]


@admin.register(DoctorDocumentProfile)
class DoctorDocumentProfileAdmin(admin.ModelAdmin):
    list_display = ("doctor", "professional_title", "registration_number")

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)