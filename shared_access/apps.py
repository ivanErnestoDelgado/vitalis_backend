from django.apps import AppConfig


class SharedAccessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared_access'

    def ready(self):
        import shared_access.signals