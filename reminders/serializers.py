from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Reminder, ReminderAccess,ReminderLog
from medications.models import Medication
from shared_access.models import SharedAccess 
from django.db import models 
from users.serializers import UserSerializer

User = get_user_model()


# ===============================
# ReminderAccessSerializer
# ===============================
class ReminderAccessSerializer(serializers.ModelSerializer):
    user_info=UserSerializer(source="user", read_only=True)

    class Meta:
        model = ReminderAccess
        fields = [
            "id",
            "reminder",
            "user",
            "user_info" ,
            "can_edit",
            "can_delete",
            "receive_notifications",
            "added_at",
        ]
        read_only_fields = ["id", "added_at", "user_email", "user_id"]

    def validate(self, attrs):
        reminder = attrs["reminder"]
        target_user = attrs["user"]
        user = self.context["request"].user

        # Solo el paciente o el creador pueden compartir el reminder
        if (reminder.patient != user) and (reminder.created_by != user):
            raise serializers.ValidationError(
                "Solo el paciente o el creador del recordatorio pueden compartirlo."
            )

        # Evitar que el mismo usuario se comparta a sí mismo
        if attrs["user"] == reminder.patient:
            raise serializers.ValidationError("El paciente ya tiene acceso al recordatorio.")
        

        shared_exists = SharedAccess.objects.filter(
            (models.Q(owner=reminder.patient, shared_with=target_user) |
             models.Q(owner=target_user, shared_with=reminder.patient)),
        ).exists()

        if not shared_exists:
            raise serializers.ValidationError(
                "No existe un acceso compartido activo entre el paciente y este usuario."
            )

        return attrs


# ===============================
# ReminderSerializer
# ===============================
class ReminderSerializer(serializers.ModelSerializer):
    shared_with = ReminderAccessSerializer(source="shared_with.all", many=True, read_only=True)
    medication_name = serializers.CharField(source="medication.name", read_only=True)
    patient_email = serializers.EmailField(source="patient.email", read_only=True)
    patient_name=serializers.CharField(source="patient.first_name", read_only=True)
    patient_last_name=serializers.CharField(source="patient.last_name", read_only=True)
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    patient = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Reminder
        fields = [
            "id",
            "patient",
            "patient_email",
            "patient_name",
            "patient_last_name",
            "medication",
            "medication_name",
            "title",
            "message",
            "start_time",
            "frequency",
            "interval_hours",
            "is_active",
            "created_at",
            "created_by",
            "created_by_email",
            "shared_with",
            "next_trigger_time",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "patient_email",
            "created_by_email",
            "shared_with",
            "next_trigger_time",
            "patient_name",
            "patient_last_name"
        ]

    def create(self, validated_data):
        """
        Define quién es el paciente y el creador según el contexto.
        """
        request = self.context.get("request")
        user = request.user if request else None

        # Si no se proporciona paciente, se asume que el creador es el propio paciente.
        if not validated_data.get("patient"):
            validated_data["patient"] = user
            validated_data["created_by"] = user
        else:
            # Si se está creando en nombre de un paciente (ej. doctor o cuidador)
            validated_data["created_by"] = user
        if(validated_data["frequency"]=="daily"):
            validated_data["next_trigger_time"]=validated_data["start_time"] + timezone.timedelta(days=1)
            validated_data["interval_hours"]=24
        if(validated_data["frequency"]=="custom" and validated_data.get("interval_hours")):
            validated_data["next_trigger_time"]=validated_data["start_time"] + timezone.timedelta(hours=validated_data["interval_hours"])
        reminder = super().create(validated_data)
        return reminder

    def to_representation(self, instance):
        """
        Añade campo 'total_shared' y lista simplificada de usuarios con acceso.
        """
        data = super().to_representation(instance)
        data["total_shared"] = instance.shared_with.count()
        data["shared_users"] = [
            {
                "id": a.user.id,
                "email": a.user.email,
                "can_edit": a.can_edit,
                "receive_notifications": a.receive_notifications,
            }
            for a in instance.shared_with.all()
        ]
        return data


# ===============================
# ReminderLogSerializer
# ===============================
class ReminderLogSerializer(serializers.ModelSerializer):
    reminder_title = serializers.CharField(source="reminder.title", read_only=True)
    medication_name = serializers.CharField(source="reminder.medication.name", read_only=True)

    class Meta:
        model = ReminderLog
        fields = ["id", "reminder", "reminder_title", "medication_name", "taken_at", "was_taken", "notes"]
        read_only_fields = ["id", "taken_at", "reminder_title", "medication_name"]

    def validate(self, attrs):
        user = self.context["request"].user
        reminder = attrs.get("reminder")

        if not reminder:
            raise serializers.ValidationError("Se requiere un recordatorio válido.")

        # Validar acceso
        if not reminder.has_access(user):
            raise serializers.ValidationError("No tienes permiso para registrar logs en este recordatorio.")

        return attrs