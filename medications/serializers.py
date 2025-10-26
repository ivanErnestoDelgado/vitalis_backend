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
        read_only_fields=['doctor']


    def validate(self, attrs):
        doctor = self.context["request"].user
        patient = attrs["patient"]
        variant = attrs["drug_variant"]
        validate_doctor_patient_access(doctor, patient)
        validate_prescription_rules(doctor, variant.drug)
        return attrs
    def create(self, validated_data):
        validated_data["doctor"] = self.context["request"].user
        return super().create(validated_data)

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