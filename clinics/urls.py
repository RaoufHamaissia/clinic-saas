from django.urls import path
from . import views

app_name = "clinics"

urlpatterns = [
    path("register/", views.register_clinic, name="register"),
    path("specialties/suggest/", views.specialty_suggest, name="specialty_suggest"),

    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/add/", views.add_doctor, name="doctor_add"),
    
    path("secretaries/", views.secretary_list, name="secretary_list"),
    path("secretaries/add/", views.add_secretary, name="secretary_add"),

    path("settings/", views.clinic_settings, name="settings"),
]
