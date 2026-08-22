from contextvars import ContextVar

_current_clinic: ContextVar = ContextVar("current_clinic", default=None)

def set_current_clinic(clinic):
    _current_clinic.set(clinic)

def get_current_clinic():
    return _current_clinic.get()

def clear_current_clinic():
    _current_clinic.set(None)