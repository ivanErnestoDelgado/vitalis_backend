from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import models

from .models import SharedAccess, SharedAccessToken, AccessHistory
from .serializers import (
    SharedAccessSerializer,
    SharedAccessTokenSerializer,
    SharedAccessInvitationSerializer,
    AccessHistorySerializer
)


class SharedAccessViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SharedAccessSerializer
    queryset = SharedAccess.objects.all()

    def get_queryset(self):
        user = self.request.user
        return SharedAccess.objects.filter(owner=user) | SharedAccess.objects.filter(shared_with=user)

    # --- Flujo 1: Invitaciones manuales ---
    @action(detail=False, methods=['post'])
    def invite(self, request):
        serializer = SharedAccessInvitationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        access = serializer.save()
        return Response(SharedAccessSerializer(access).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        access = self.get_object()
        if access.shared_with != request.user:
            return Response({"detail": "You cannot accept this invitation."}, status=403)
        access.status = 'accepted'
        access.save()
        return Response(SharedAccessSerializer(access).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        access = self.get_object()
        if access.shared_with != request.user:
            return Response({"detail": "You cannot reject this invitation."}, status=403)
        access.status = 'rejected'
        access.save()
        return Response({"detail": "Invitation rejected."})

    # --- Flujo 2: QR ---
    @action(detail=False, methods=['post'])
    def generate_qr_token(self, request):
        """Genera un token temporal asociado al usuario autenticado."""
        user = request.user
        token = SharedAccessToken.objects.create(owner=user)
        return Response(SharedAccessTokenSerializer(token).data)

    @action(detail=False, methods=['post'])
    def connect_via_qr(self, request):
        """Permite conectar a un paciente escaneando un token QR."""
        token_str = request.data.get('token')
        role = request.data.get('role', 'family')

        try:
            token = SharedAccessToken.objects.get(token=token_str)
        except SharedAccessToken.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=400)

        if not token.is_valid():
            return Response({"detail": "Token expired"}, status=400)

        owner = token.owner
        shared_with = request.user

        if owner == shared_with:
            return Response({"detail": "You cannot connect with yourself"}, status=400)

        access, created = SharedAccess.objects.get_or_create(
            owner=owner,
            shared_with=shared_with,
            defaults={'role': role, 'status': 'accepted'}
        )

        if not created:
            return Response({"detail": "Access already exists"}, status=400)

        return Response(SharedAccessSerializer(access).data, status=201)
    
    @action(detail=True, methods=['delete'])
    def revoke(self, request, pk=None):
        """
        Permite al propietario (paciente) revocar el acceso a su información
        de un doctor o familiar.
        """
        access = self.get_object()

        # Solo el owner puede revocar accesos
        if access.owner != request.user:
            return Response(
                {"detail": "No tienes permiso para revocar este acceso."},
                status=status.HTTP_403_FORBIDDEN,
            )

        access.delete()
        return Response({"detail": "Acceso revocado correctamente."}, status=status.HTTP_204_NO_CONTENT)
    
class AccessHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Permite consultar el historial de accesos relacionados con el usuario autenticado.
    """
    serializer_class = AccessHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Filtra los registros donde el usuario fue dueño o receptor del acceso
        return AccessHistory.objects.filter(
            models.Q(owner=user) | models.Q(shared_with=user)
        ).order_by("-timestamp")