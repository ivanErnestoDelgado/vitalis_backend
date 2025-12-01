from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from reminders.models import Reminder
from users.models import CustomFCMDevice

import logging
logger = logging.getLogger(__name__)


def send_push_to_reminder_users(reminder: Reminder):
    """Obtiene el paciente, creador y usuarios con acceso y les envía push."""

    users_to_notify = reminder.get_all_receivers()

    devices = CustomFCMDevice.objects.filter(user__in=users_to_notify)

    if not devices.exists():
        logger.info(f"No hay dispositivos FCM para reminder {reminder.id}")
        return

    payload = {
        "title": reminder.title,
        "body": reminder.message or "Tienes un recordatorio pendiente.",
        "reminder_id": reminder.id,
    }

    devices.send_message(
        title=payload["title"],
        body=payload["body"],
        data=payload,
        sound="default",
    )

    logger.info(f"Notificaciones enviadas para reminder {reminder.id}")


def update_next_trigger(reminder):
    """Genera el siguiente horario según la frecuencia."""
    if reminder.frequency == "once":
        reminder.is_active = False
        return

    if reminder.frequency == "daily":
        reminder.next_trigger_time += timezone.timedelta(days=1)
        return

    if reminder.frequency == "hourly":
        reminder.next_trigger_time += timezone.timedelta(hours=1)
        return

    if reminder.frequency == "custom" and reminder.interval_hours:
        reminder.next_trigger_time += timezone.timedelta(hours=reminder.interval_hours)
        return


def process_reminders():
    """Procesa los reminders cuya hora de disparo ya llegó."""
    now = timezone.now()

    due_reminders = Reminder.objects.filter(
        is_active=True,
        next_trigger_time__lte=now
    ).select_related("patient", "created_by")

    if not due_reminders.exists():
        return

    logger.info(f"Procesando {due_reminders.count()} recordatorios pendientes...")

    for reminder in due_reminders:
        if reminder.medication.end_date and reminder.medication.end_date < now.date():
            reminder.is_active = False
            reminder.save()
            logger.info(f"Reminder {reminder.id} desactivado (medicación finalizada).")
            continue

        with transaction.atomic():
            send_push_to_reminder_users(reminder)
            update_next_trigger(reminder)
            reminder.save()

    logger.info("Procesamiento completado.")


scheduler = None


def start_reminder_scheduler():
    """
    Inicia solo 1 instancia del scheduler global, incluso en producción.
    """
    global scheduler

    if scheduler and scheduler.running:
        logger.info("Scheduler ya estaba iniciado, se omite.")
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(process_reminders, "interval", seconds=30)
    scheduler.start()

    logger.info("Reminder Scheduler iniciado correctamente.")
