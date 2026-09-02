from django.urls import path
from .views import audit_log_view, dashboard


app_name = "core"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("audit-log/", audit_log_view, name="audit_log"),
]
