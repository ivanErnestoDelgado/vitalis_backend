from rest_framework import viewsets, permissions
from .models import Drug, DrugVariant, Diagnosis, Medication, UnsafeMedication
from .serializers import (
    DrugSerializer, DrugVariantSerializer, DiagnosisSerializer,
    MedicationSerializer, UnsafeMedicationSerializer,DrugWithVariantsSerializer
)
from utils.permissions import IsAdminOrReadOnly, IsDoctor
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .validators import *
from users.models import User




class DrugViewSet(viewsets.ModelViewSet):
    queryset = Drug.objects.all()
    serializer_class = DrugSerializer
    permission_classes = [IsAdminOrReadOnly]
    @action(detail=False, methods=["get"], url_path="with-variants")
    def list_with_variants(self, request):
        """
        Retorna todos los medicamentos junto con sus variantes.
        """
        drugs = Drug.objects.prefetch_related("variants").all()
        serializer = DrugWithVariantsSerializer(drugs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DrugVariantViewSet(viewsets.ModelViewSet):
    queryset = DrugVariant.objects.all()
    serializer_class = DrugVariantSerializer
    permission_classes = [IsAdminOrReadOnly]


class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [IsDoctor]
    #Endpoint para que el paciente vea sus diagnósticos
    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_diagnoses(self, request):
        user = request.user
        diagnoses = Diagnosis.objects.filter(patient=user).order_by("-created_at")
        serializer = self.get_serializer(diagnoses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DoctorMedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.filter(created_by_patient=False)
    serializer_class = MedicationSerializer
    permission_classes = [IsDoctor]

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_medications(self, request):
        user = request.user
        meds = Medication.objects.filter(patient=user).order_by("-created_at")
        serializer = self.get_serializer(meds, many=True)
        return Response(serializer.data)
    
class PatientMedicationViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Medication.objects.filter(
            patient=self.request.user,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(patient=self.request.user, created_by_patient=True)



class PatientUnsafeMedicationViewSet(viewsets.ModelViewSet):
    """
    Endpoint para que el paciente gestione sus propios medicamentos inseguros.
    """
    serializer_class = UnsafeMedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UnsafeMedication.objects.filter(patient=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        # Forzamos que el paciente autenticado sea el propietario
        serializer.save(patient=self.request.user, added_by=self.request.user)

class DoctorUnsafeMedicationViewSet(viewsets.ModelViewSet):
    """
    Permite al doctor consultar y registrar medicamentos inseguros
    para pacientes con los que tiene acceso compartido.
    """
    serializer_class = UnsafeMedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Por defecto, no devuelve nada hasta que se especifique un paciente.
        """
        return UnsafeMedication.objects.none()

    @action(detail=False, methods=["get"])
    def list_by_patient(self, request):
        """
        Permite al doctor consultar los medicamentos inseguros
        de un paciente con el que tenga acceso compartido.
        """
        patient_id = request.query_params.get("patient_id")

        if not patient_id:
            raise PermissionDenied("Debes especificar el parámetro 'patient_id'.")

        try:
            patient = User.objects.get(id=patient_id)
        except User.DoesNotExist:
            raise PermissionDenied("El paciente especificado no existe.")

        # Validar acceso compartido (doctor ↔ paciente)
        validate_doctor_patient_access(request.user, patient)

        meds = UnsafeMedication.objects.filter(patient=patient).select_related("drug")
        serializer = self.get_serializer(meds, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        Permite al doctor registrar un medicamento inseguro
        para un paciente al que atiende.
        """
        data = request.data.copy()
        patient_id = data.get("patient")

        if not patient_id:
            raise PermissionDenied("Debes especificar el campo 'patient'.")

        try:
            patient = User.objects.get(id=patient_id)
        except User.DoesNotExist:
            raise PermissionDenied("El paciente especificado no existe.")

        # Validar que el doctor tenga acceso compartido
        validate_doctor_patient_access(request.user, patient)

        # Forzar que el campo `added_by` sea el doctor autenticado
        data["added_by"] = request.user.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)