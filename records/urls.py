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

    
]
