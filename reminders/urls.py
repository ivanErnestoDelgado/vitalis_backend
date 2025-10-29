# reminders/urls.py
from rest_framework.routers import DefaultRouter
from .views import (
    PatientReminderViewSet,
    DoctorReminderViewSet,
    PatientReminderLogViewSet,
    DoctorReminderLogViewSet,
    ReminderAccessViewSet,
)

router = DefaultRouter()

# Recordatorios principales para pacientes (creación, consulta, edición, eliminación)
router.register("patient/reminders", PatientReminderViewSet, basename="patient_reminders")

#
router.register("doctor/reminders", DoctorReminderViewSet, basename="doctor_reminders")


router.register("doctor/reminder-logs", DoctorReminderLogViewSet, basename="doctor_reminder-logs")
# Logs de recordatorios (registro de tomas, estado, observaciones)
router.register("patient/reminder-logs", PatientReminderLogViewSet, basename="reminder-logs")

# Acceso compartido (cuidador ↔ paciente)
router.register("reminder-access", ReminderAccessViewSet, basename="reminder-access")

urlpatterns = router.urls
