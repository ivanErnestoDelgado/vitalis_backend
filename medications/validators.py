from rest_framework.exceptions import ValidationError
from shared_access.models import SharedAccess

def validate_doctor_patient_access(doctor, patient):
    if not SharedAccess.objects.filter(shared_with=doctor, owner=patient, status="accepted",role="doctor").exists():
        raise ValidationError("El doctor no tiene acceso compartido con este paciente.")


def validate_prescription_rules(creator, drug):
    if drug.prescription_required and not hasattr(creator, 'doctor_profile'):
        raise ValidationError("Solo los doctores pueden prescribir este medicamento.")
