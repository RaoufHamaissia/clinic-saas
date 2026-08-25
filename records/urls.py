from django.urls import path
from . import views

app_name = "records"

urlpatterns = [
    path("prescriptions/", views.prescription_list, name="prescription_list"),
    path("prescriptions/add/", views.add_prescription, name="prescription_add"),
    path("prescriptions/<int:pk>/print/", views.prescription_print, name="prescription_print"),
    path("medications/suggest/", views.medication_suggest, name="medication_suggest"),
]
