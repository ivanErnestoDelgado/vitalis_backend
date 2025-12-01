from django.apps import AppConfig
import os
import threading


class RemindersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reminders'
    def ready(self):
        """
        Inicia el scheduler solo cuando Django arranca.
        Evita ejecución múltiple en auto-reload o workers adicionales.
        """

        # Evitar ejecución en threads secundarios
        if threading.current_thread().name != "MainThread":
            return

        # Evitar ejecución en migraciones
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .scheduler import start_reminder_scheduler

        print("[Reminders] Inicializando scheduler de recordatorios...")
        start_reminder_scheduler()