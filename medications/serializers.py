from rest_framework import serializers
from .models import Drug, DrugVariant, Diagnosis, Medication, UnsafeMedication
from .validators import validate_doctor_patient_access, validate_prescription_rules


class DrugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drug
        fields = "__all__"


class DrugVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugVariant
        fields = "__all__"


class DrugWithVariantsSerializer(serializers.ModelSerializer):
    variants = DrugVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Drug
        fields = [
            "id",
            "name",
            "description",
            "prescription_required",
            "created_at",
            "variants",
        ]

class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = ['doctor','patient','description']
        read_only_fields=['doctor']

    def validate(self, attrs):
        doctor = self.context["request"].user
        patient = attrs["patient"]
        validate_doctor_patient_access(doctor, patient)
        return attrs
    def create(self, validated_data):
        validated_data["doctor"] = self.context["request"].user
        return super().create(validated_data)

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = "__all__"
        read_only_fields = ["doctor", "created_by_patient"]

    def validate(self, attrs):
        user = self.context["request"].user
        variant = attrs["drug_variant"]
        drug = variant.drug

        # ============================
        # 1) VALIDACIÓN DE MEDICACIÓN INSEGURA
        # ============================
        patient = attrs.get("patient", user)
        unsafe_exists = UnsafeMedication.objects.filter(
            patient=patient,
            drug=drug
        ).exists()

        if unsafe_exists:
            raise serializers.ValidationError(
                f"El medicamento '{drug.name}' está marcado como inseguro para este paciente."
            )

        # ============================
        # 2) SI ES PACIENTE → SELF MEDICATION
        # ============================
        if not hasattr(user,"doctor_profile"):
            # Solo aplica cuando el paciente crea su propia medicación
            attrs["patient"] = user
            attrs["created_by_patient"] = True

            # Medicamentos que requieren receta NO pueden ser automedicados
            if drug.prescription_required:
                raise serializers.ValidationError(
                    f"El medicamento '{drug.name}' requiere prescripción médica."
                )

            # No se debe enviar campo doctor
            if "doctor" in attrs:
                attrs.pop("doctor", None)

            return attrs

        # ============================
        # 3) SI ES DOCTOR → PRESCRIPCIÓN FORMAL
        # ============================
        doctor = user
        patient = attrs["patient"]

        validate_doctor_patient_access(doctor, patient)
        validate_prescription_rules(doctor, drug)

        attrs["doctor"] = doctor
        attrs["created_by_patient"] = False

        return attrs

class UnsafeMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnsafeMedication
        fields = "__all__"

    def validate(self, attrs):
        user = self.context["request"].user
        patient = attrs["patient"]

        # Si el usuario es el propio paciente, permitido
        if user == patient:
            return attrs

        # Si es doctor, validar acceso compartido
        validate_doctor_patient_access(user, patient)
        return attrs