from django.urls import path
from . import views

app_name = "clinics"

urlpatterns = [
    path("register/", views.register_clinic, name="register"),  #type:ignore
]
