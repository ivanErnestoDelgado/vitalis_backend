# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from .models import Role, UserRole, PatientProfile, FamilyProfile, DoctorProfile
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError("Credenciales inválidas")

        refresh = RefreshToken.for_user(user)

        # Detectar roles
        roles = []
        if hasattr(user, "patient_profile"):
            roles.append("patient")
        if hasattr(user, "doctor_profile"):
            roles.append("doctor")
        if hasattr(user, "family_profile"):
            roles.append("family")

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "roles": roles,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone_number", "password"]

    def create(self, validated_data):
        # Crear usuario
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Crear perfiles automáticamente
        PatientProfile.objects.create(user=user)
        FamilyProfile.objects.create(user=user)

        return user

    
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name"]


class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "role", "assigned_at"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "created_at",
            "roles",
        ]
        read_only_fields = ["roles"]


# Perfiles extendidos
class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ["id", "medical_history"]


class FamilyProfileSerializer(serializers.ModelSerializer):
    related_patients = PatientProfileSerializer(many=True, read_only=True)

    class Meta:
        model = FamilyProfile
        fields = ["id", "related_patients"]


class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ["id", "license_number", "specialty"]