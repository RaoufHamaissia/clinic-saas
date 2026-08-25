from django.urls import path
from . import views

app_name = "records"

urlpatterns = [
    path("prescriptions/", views.prescription_list, name="prescription_list"),
    path("prescriptions/add/", views.add_prescription, name="prescription_add"),
    path("prescriptions/<int:pk>/print/", views.prescription_print, name="prescription_print"),

    path("medications/suggest/", views.medication_suggest, name="medication_suggest"),

    path("notes/", views.note_list, name="note_list"),
    path("notes/add/", views.add_note, name="note_add"),
    path("notes/<int:pk>/print/", views.note_print, name="note_print"),

    path("procedure-reports/", views.procedure_report_list, name="procedure_report_list"),
    path("procedure-reports/add/", views.add_procedure_report, name="procedure_report_add"),
    path("procedure-reports/<int:pk>/print/", views.procedure_report_print, name="procedure_report_print"),

    path("labwork-demands/", views.labwork_demand_list, name="labwork_demand_list"),
    path("labwork-demands/add/", views.add_labwork_demand, name="labwork_demand_add"),
    path("labwork-demands/<int:pk>/print/", views.labwork_demand_print, name="labwork_demand_print"),

    path("document-profile/", views.edit_document_profile, name="edit_document_profile"),

]
