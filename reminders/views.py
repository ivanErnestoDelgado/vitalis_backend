from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from utils.permissions import IsDoctor
from shared_access.models import SharedAccess
from rest_framework.exceptions import PermissionDenied

from .models import Reminder, ReminderLog, ReminderAccess
from .serializers import (
    ReminderSerializer,
    ReminderLogSerializer,
    ReminderAccessSerializer,
)
from medications.validators import validate_doctor_patient_access
from django.contrib.auth import get_user_model

User = get_user_model()


# ===============================
# Vistas de paciente
# ===============================
class PatientReminderViewSet(viewsets.ModelViewSet):
    """
    Paciente gestiona sus recordatorios y ve recordatorios compartidos con él/ella
    (incluyendo los creados por su doctor o familiares).
    """
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Reminder.objects.filter(
                models.Q(patient=user) | models.Q(shared_with__user=user)
            )
            .distinct()
            .select_related("patient", "created_by", "medication")
            .prefetch_related("shared_with__user")
        )

    def perform_create(self, serializer):
        """
        El paciente crea su propio recordatorio.
        """
        serializer.save(patient=self.request.user, created_by=self.request.user)



class PatientReminderLogViewSet(viewsets.ModelViewSet):
    """
    Paciente o cuidador pueden registrar si se tomó o no un medicamento asociado a un Reminder.
    """
    serializer_class = ReminderLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            ReminderLog.objects.filter(
                models.Q(reminder__patient=user)
                | models.Q(reminder__shared_with__user=user)
            )
            .distinct()
            .select_related("reminder", "reminder__medication")
        )

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=["post"], url_path="confirm")
    def confirm_medication(self, request):
        """
        Permite que un paciente o cuidador confirme si el medicamento fue tomado.
        Ejemplo JSON:
        {
            "reminder_id": 12,
            "was_taken": true,
            "notes": "El paciente lo tomó a tiempo"
        }
        """ 
        reminder_id = request.data.get("reminder_id")
        was_taken = request.data.get("was_taken")
        notes = request.data.get("notes", "")

        if reminder_id is None or was_taken is None:
            return Response(
                {"detail": "Los campos 'reminder_id' y 'was_taken' son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reminder = get_object_or_404(Reminder, id=reminder_id)

        # Validar acceso del usuario (paciente, creador o cuidador)
        user = request.user
        if not reminder.has_access(user):
            return Response(
                {"detail": "No tienes permiso para confirmar este recordatorio."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Crear el log de confirmación
        reminder_log = ReminderLog.objects.create(
            reminder=reminder,
            was_taken=was_taken,
            notes=notes,
        )

        serializer = ReminderLogSerializer(reminder_log)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ===============================
# Vistas de doctor
# ===============================
class DoctorReminderViewSet(viewsets.ModelViewSet):
    """
    Los doctores pueden crear, editar o eliminar recordatorios de pacientes
    con los que tengan una relación 'SharedAccess' aceptada (role='doctor').
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = ReminderSerializer

    def get_queryset(self):
        doctor = self.request.user
        # El doctor solo ve recordatorios creados por él
        return Reminder.objects.filter(created_by=doctor)

    def _check_doctor_access(self, patient):
        """
        Valida si el doctor tiene acceso al paciente.
        Lanza excepción si no lo tiene.
        """
        doctor = self.request.user
        has_access = SharedAccess.objects.filter(
            owner=patient,
            shared_with=doctor,
            role="doctor",
            status="accepted"
        ).exists()

        if not has_access:
            raise PermissionDenied(
                detail="No tienes un acceso activo con este paciente."
            )

    def perform_create(self, serializer):
        doctor = self.request.user
        patient = serializer.validated_data.get("patient")

        #Validar acceso antes de crear
        self._check_doctor_access(patient)

        reminder = serializer.save(created_by=doctor, patient=patient)

        # Registrar el acceso automático del paciente
        ReminderAccess.objects.get_or_create(
            reminder=reminder,
            user=doctor,
            can_edit=True,
            can_delete=True
        )

        return reminder

    def update(self, request, *args, **kwargs):
        """
        Permite actualizar un reminder solo si el doctor mantiene acceso al paciente.
        """
        instance = self.get_object()
        self._check_doctor_access(instance.patient)

        # Actualiza el recordatorio
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        reminder = serializer.save()
        return Response(ReminderSerializer(reminder).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Permite eliminar un reminder solo si el doctor mantiene acceso aceptado.
        """
        instance = self.get_object()
        self._check_doctor_access(instance.patient)
        instance.delete()
        return Response({"detail": "Recordatorio eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)

class DoctorReminderLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Doctor únicamente consulta logs de pacientes que atiende.
    """
    serializer_class = ReminderLogSerializer
    permission_classes = [permissions.IsAuthenticated,IsDoctor]

    def get_queryset(self):
        user = self.request.user
        patient_id = self.request.query_params.get("patient")
        if not patient_id:
            return ReminderLog.objects.none()

        validate_doctor_patient_access(user, patient_id)
        return (
            ReminderLog.objects.filter(reminder__patient_id=patient_id)
            .select_related("reminder", "reminder__medication")
        )


# ===============================
# Vista de compartir acceso
# ===============================
class ReminderAccessViewSet(viewsets.ModelViewSet):
    """
    Permite compartir o revocar acceso a recordatorios con familiares o cuidadores.
    Solo el paciente o el creador del recordatorio pueden otorgar acceso.
    """
    serializer_class = ReminderAccessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Mostrar accesos de recordatorios donde el usuario es paciente o creador
        return (
            ReminderAccess.objects.filter(
                models.Q(reminder__patient=user) | models.Q(reminder__created_by=user)
            )
            .select_related("reminder", "user")
            .distinct()
        )

    def perform_create(self, serializer):
        serializer.save()
        

    @action(detail=True, methods=["patch"], url_path="toggle-notifications")
    def toggle_notifications(self, request, pk=None):
        """
        Permite que el usuario modifique el valor de receive_notifications (True/False)
        """
        access = get_object_or_404(ReminderAccess, pk=pk)

        # Validar que el usuario tenga permiso (solo el asignado o el paciente/creador)
        user = request.user
        if not (
            access.user == user
            or access.reminder.patient == user
            or access.reminder.created_by == user
        ):
            return Response(
                {"detail": "No tienes permiso para modificar las notificaciones de este acceso."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Obtener nuevo valor del body
        new_value = request.data.get("receive_notifications")
        if new_value is None:
            return Response(
                {"detail": "Debe especificar el campo 'receive_notifications'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access.receive_notifications = bool(new_value)
        access.save()

        return Response(
            {
                "id": access.id,
                "receive_notifications": access.receive_notifications,
                "message": f"Notificaciones {'activadas' if access.receive_notifications else 'desactivadas'} correctamente.",
            },
            status=status.HTTP_200_OK,
        )
    @action(detail=True, methods=["post"], url_path="remove")
        # permite remover un acceso compartido
    def remove_access(self, request, pk=None):
        access = get_object_or_404(ReminderAccess, pk=pk)
        reminder = access.reminder
        user = request.user

        if reminder.patient != user and reminder.created_by != user:
            return Response(
                {"detail": "No tienes permiso para eliminar este acceso."},
                status=status.HTTP_403_FORBIDDEN,
            )

        access.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
