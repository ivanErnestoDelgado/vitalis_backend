import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from users.models import User  


class SharedAccess(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    ROLE_CHOICES = [
        ('family', 'Family'),
        ('doctor', 'Doctor'),
    ]

    owner = models.ForeignKey(
        User,
        related_name="shared_with_others",
        on_delete=models.CASCADE
    )
    shared_with = models.ForeignKey(
        User,
        related_name="access_to_others",
        on_delete=models.CASCADE
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='family')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('owner', 'shared_with')  # evita duplicados

    def __str__(self):
        return f"{self.owner.user.email} → {self.shared_with.user.email} ({self.status})"


class SharedAccessToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Token for {self.owner.user.email} (expires {self.expires_at})"

class AccessHistory(models.Model):
    ACTION_CHOICES = [
        ("granted", "Acceso concedido"),
        ("revoked", "Acceso revocado"),
        ("accepted", "Acceso aceptado"),
        ("invited", "Invitación enviada"),
    ]

    shared_access = models.ForeignKey(
        "SharedAccess",
        on_delete=models.SET_NULL,
        null=True,
        related_name="history",
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="access_history_owner",
    )
    shared_with = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="access_history_shared",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_action_display()} - {self.shared_with} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
