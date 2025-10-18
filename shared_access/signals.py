from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SharedAccess, AccessHistory

@receiver(post_save, sender=SharedAccess)
def create_access_history_on_save(sender, instance, created, **kwargs):
    """
    Registra eventos al crear o aceptar accesos.
    """
    if created:
        action = "invited"
    elif instance.status is "accepted":
        action = "accepted"
    else:
        return  # No registra otras actualizaciones

    AccessHistory.objects.create(
        shared_access=instance,
        owner=instance.owner.user if hasattr(instance.owner, "user") else None,
        shared_with=instance.shared_with.user if hasattr(instance.shared_with, "user") else None,
        action=action,
    )

@receiver(post_delete, sender=SharedAccess)
def create_access_history_on_delete(sender, instance, **kwargs):
    """
    Registra un evento cuando un acceso es revocado.
    """
    AccessHistory.objects.create(
        shared_access=None,  # ya fue eliminado
        owner=instance.owner.user if hasattr(instance.owner, "user") else None,
        shared_with=instance.shared_with.user if hasattr(instance.shared_with, "user") else None,
        action="revoked",
    )
