from .context import set_current_clinic, clear_current_clinic

from django.conf import settings

class CurrentClinicMiddleware:
    """
    Stashes request.user.clinic in a context var for the duration of the request,
    so ClinicManager can auto-scope querysets without every view/service 
    having to pass `clinic` explicitly.

    Django admin is deliberately  left unscoped  (context var stays None)
    since it's platform-staff tooling, not clinic-user tooling.

    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin_path = request.path.startswith(f"/{settings.ADMIN_URL if hasattr(settings, 'ADMIN_URL') else 'admin'}/")

        if not is_admin_path:
            clinic = getattr(getattr(request, "user", None), "clinic", None)
            set_current_clinic(clinic)

        try:
            response = self.get_response(request)
        finally:
            clear_current_clinic()

        return response