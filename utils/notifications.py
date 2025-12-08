from fcm_django.models import FCMDevice

def send_reminder_push(reminder):
    users = reminder.get_all_receivers()

    # Filtrar solo usuarios que tienen receive_notifications=True
    receivers = []
    for access in reminder.shared_with.all():
        if access.receive_notifications:
            receivers.append(access.user)

    # Añadir paciente si corresponde
    if reminder.patient:
        receivers.append(reminder.patient)

    # Quitar duplicados
    receivers = list(set(receivers))
    
    # Obtener dispositivos
    devices = FCMDevice.objects.filter(user__in=receivers)

    # Enviar
    if devices.exists():
        devices.send_message(
            title=f"Recordatorio: {reminder.title}",
            body=reminder.message or "Es hora de tomar tu medicamento",
            data={"reminder_id": reminder.id}
        )
