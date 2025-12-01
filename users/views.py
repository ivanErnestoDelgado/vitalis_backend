from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .permissions import IsCaregiverOfPatient,IsDoctorOfPatient
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.views import APIView

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Role, UserRole, PatientProfile, FamilyProfile, DoctorProfile, CustomFCMDevice
from .serializers import (
    UserSerializer, RoleSerializer,
    PatientProfileSerializer, FamilyProfileSerializer, DoctorProfileSerializer,LoginSerializer,
    RegisterSerializer
)

User = get_user_model()

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes=[IsAdminUser]

    @action(detail=True, methods=["post"])
    def assign_role(self, request, pk=None):
        """Asigna un rol a un usuario"""
        user = self.get_object()
        role_name = request.data.get("role")

        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

        UserRole.objects.get_or_create(user=user, role=role)
        return Response({"status": f"Role '{role_name}' assigned to {user.username}"})

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class PatientProfileViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAdminUser]
    queryset = PatientProfile.objects.all()
    serializer_class = PatientProfileSerializer


class FamilyProfileViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAdminUser]
    queryset = FamilyProfile.objects.all()
    serializer_class = FamilyProfileSerializer


class DoctorProfileViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAdminUser]
    queryset = DoctorProfile.objects.all()
    serializer_class = DoctorProfileSerializer

class PatientDetailForFamily(APIView):
    permission_classes = [IsAuthenticated, IsCaregiverOfPatient]

    def get(self, request, patient_id):
        patient = PatientProfile.objects.get(id=patient_id)
        return Response({
            "id": patient.id,
            "user": {
                "first_name": patient.user.first_name,
                "last_name": patient.user.last_name,
                "email": patient.user.email,
            }
        })

class PatientDetailForDoctor(APIView):
    permission_classes = [IsAuthenticated, IsDoctorOfPatient]

    def get(self, request, patient_id):
        patient = PatientProfile.objects.get(id=patient_id)
        return Response({
            "id": patient.id,
            "user": {
                "first_name": patient.user.first_name,
                "last_name": patient.user.last_name,
                "email": patient.user.email,
            }
        })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    token = request.data.get("fcm_token")

    if not token:
        return Response({"detail": "El token FCM es requerido."}, status=400)

    device, created = CustomFCMDevice.objects.update_or_create(
        user=request.user,
        defaults={
            "registration_id": token,
            "type": "android",
            "active": True
        }
    )

    return Response({
        "detail": "Token registrado correctamente.",
        "created": created
    })