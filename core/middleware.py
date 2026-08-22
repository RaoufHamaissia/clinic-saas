from .context import set_current_clinic, clear_current_clinic

class CurrentClinicMiddleware:
    """
    Stashes request.user.clinic in a context var for the duration of the request,
    so ClinicManager can auto-scope querysets without every view/service 
    having to pass `clinic` explicitly.

    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        clinic = getattr(getattr(request, "user", None), "clinic", None)
        set_current_clinic(clinic)

        try:
            response = self.get_response(request)
        finally:
            clear_current_clinic()

        return response