from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Reminder(models.Model):
    FREQUENCY_CHOICES = [
        ("once", "Una vez"),
        ("daily", "Diario"),
        ("weekly", "Semanal"),
        ("custom", "Personalizado"),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reminders")
    medication = models.ForeignKey("medications.Medication", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    start_time = models.DateTimeField()
    frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES, default="once")
    interval_hours = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_reminders")
    next_trigger_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reminder for {self.patient} - {self.title}"

    def has_access(self, user):
        """
        Devuelve True si el usuario tiene acceso al recordatorio:
         - Es el paciente
         - Es quien creó el reminder
         - Está en ReminderAccess.shared_with
        """
        if not user:
            return False
        if user == self.patient:
            return True
        if self.created_by and user == self.created_by:
            return True
        return self.shared_with.filter(user=user).exists()

    def get_all_receivers(self):
        """
        Devuelve todos los usuarios que deben recibir notificación de este recordatorio:
        el paciente, el creador y los usuarios compartidos.
        """
        users = {self.patient, self.created_by}

        for access in self.shared_with.filter(receive_notifications=True):
            users.add(access.user)

        return list(users)  


class ReminderAccess(models.Model):
    """
    Define qué usuarios tienen acceso a un Reminder específico.
    Ejemplo: un familiar o cuidador que puede ver y recibir notificaciones.
    """
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name="shared_with")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accessible_reminders")
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    receive_notifications = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("reminder", "user")

    def __str__(self):
        return f"{self.user} tiene acceso a {self.reminder}"



class ReminderLog(models.Model):
    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name="logs")
    taken_at = models.DateTimeField(auto_now_add=True)
    was_taken = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.reminder.title} - {'Taken' if self.was_taken else 'Missed'} at {self.taken_at}"
