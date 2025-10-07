from rest_framework.permissions import BasePermission
from .models import PatientProfile

class IsDoctorOfPatient(BasePermission):
    """
    Permite acceso solo si el usuario es doctor y está asignado al paciente consultado.
    Requiere que la vista tenga un parámetro 'patient_id' en la URL o request.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # El usuario debe tener perfil de doctor
        if not hasattr(request.user, "doctor_profile"):
            return False

        patient_id = view.kwargs.get("patient_id")
        if not patient_id:
            return False

        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return False

        # Aquí verificamos asignación: se puede tener una relación DoctorProfile -> PatientProfile
        # Por simplicidad, asumimos que cada paciente tiene un campo `assigned_doctors`
        return patient.assigned_doctors.filter(id=request.user.doctor_profile.id).exists()

class IsCaregiverOfPatient(BasePermission):
    """
    Permite acceso solo si el usuario es familiar y cuidador del paciente consultado.
    Requiere que la vista tenga un parámetro 'patient_id' en la URL o en la request.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # El familiar debe tener un perfil de familia
        if not hasattr(request.user, "family_profile"):
            return False

        patient_id = view.kwargs.get("patient_id")  # tomado de la URL
        if not patient_id:
            return False

        # Verificamos si el paciente está en su lista de cuidados
        return request.user.family_profile.related_patients.filter(id=patient_id).exists()

class IsPatient(BasePermission):
    """
    Permite acceso solo si el usuario tiene el rol de paciente.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(role__name="patient").exists()


class IsFamily(BasePermission):
    """
    Permite acceso solo si el usuario tiene el rol de familiar.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(role__name="family").exists()


class IsDoctor(BasePermission):
    """
    Permite acceso solo si el usuario tiene el rol de doctor.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.roles.filter(role__name="doctor").exists()