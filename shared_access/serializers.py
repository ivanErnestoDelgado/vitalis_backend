from rest_framework import serializers
from .models import SharedAccess, SharedAccessToken, AccessHistory
from users.models import User

class SharedAccessSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='owner.user.email', read_only=True)
    shared_with_email = serializers.EmailField(source='shared_with.user.email', read_only=True)

    class Meta:
        model = SharedAccess
        fields = ['id', 'owner', 'owner_email', 'shared_with', 'shared_with_email', 'role', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']


class SharedAccessInvitationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    role = serializers.ChoiceField(choices=SharedAccess.ROLE_CHOICES)

    class Meta:
        model = SharedAccess
        fields = ['email', 'role']

    def create(self, validated_data):
        request = self.context['request']
        owner = request.user
        user_email = validated_data['email']
        role = validated_data['role']

        try:
            shared_with = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Usuario no encontrado"})

        if owner == shared_with:
            raise serializers.ValidationError({"email": "No de puedes invitar a ti mismo"})

        access, created = SharedAccess.objects.get_or_create(
            owner=owner,
            shared_with=shared_with,
            defaults={'role': role, 'status': 'pending'}
        )

        if not created:
            raise serializers.ValidationError({"detail": "La invitación ya existe o el accesso ya fue concedido"})

        return access


class SharedAccessTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedAccessToken
        fields = ['token', 'expires_at']
        read_only_fields = ['token', 'expires_at']


class AccessHistorySerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    shared_with_name = serializers.CharField(source="shared_with.get_full_name", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AccessHistory
        fields = [
            "id",
            "action",
            "action_display",
            "timestamp",
            "owner_name",
            "shared_with_name",
        ]
