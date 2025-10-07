from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None 
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=150, blank=True)  
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []   # no pedimos username

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"
    

class Role(models.Model):
    ROLE_CHOICES = [
        ("patient", "Patient"),
        ("family", "Family"),
        ("doctor", "Doctor"),
    ]
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "role")  # evita duplicados

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


# Ejemplo de perfiles extendidos
class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    assigned_doctors = models.ManyToManyField("DoctorProfile", related_name="patients")  # nuevos doctores asignados
    
    def __str__(self):
        return f"Patient Profile: {self.user.first_name} {self.user.last_name}"


class FamilyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="family_profile")
    related_patients = models.ManyToManyField("PatientProfile", related_name="caregivers")

    def __str__(self):
        return f"Family Profile: {self.user.username}"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    license_number = models.CharField(max_length=50)
    specialty = models.CharField(max_length=100)

    def __str__(self):
        return f"Doctor Profile: {self.user.username}"