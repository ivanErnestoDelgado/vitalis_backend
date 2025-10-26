from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """Permite edición solo al admin; lectura para todos."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsDoctor(BasePermission):
    """Solo doctores pueden crear diagnósticos o prescripciones."""
    def has_permission(self, request, view):
        return hasattr(request.user, "doctor_profile")
