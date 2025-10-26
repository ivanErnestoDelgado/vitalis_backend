from django.db import models
from django.conf import settings
from shared_access.models import SharedAccess

User = settings.AUTH_USER_MODEL


class Drug(models.Model):
    """Medicamento genérico registrado por el administrador."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    prescription_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DrugVariant(models.Model):
    """Variantes de un medicamento: presentación, dosis, fabricante."""
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name="variants")
    variant_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.drug.name} - {self.variant_name}"


class Diagnosis(models.Model):
    """Diagnóstico que solo puede emitir un doctor."""
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="diagnoses")
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patient_diagnoses")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis by {self.doctor} for {self.patient}"


class Medication(models.Model):
    """Relación entre paciente, doctor y medicamento prescrito."""
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prescribed_medications")
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="medications")
    drug_variant = models.ForeignKey(DrugVariant, on_delete=models.CASCADE)
    dosage_instructions = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.drug_variant} for {self.patient}"


class UnsafeMedication(models.Model):
    """Medicamentos que pueden ser peligrosos para un paciente."""
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="unsafe_medications")
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)
    reason = models.TextField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="unsafe_reports")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.drug.name} unsafe for {self.patient}"
