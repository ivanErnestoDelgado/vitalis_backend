from rest_framework.routers import DefaultRouter
from .views import (
    DrugViewSet, DrugVariantViewSet, DiagnosisViewSet,
    MedicationViewSet, PatientUnsafeMedicationViewSet,DoctorUnsafeMedicationViewSet
)

router = DefaultRouter()
router.register("drugs", DrugViewSet, basename="drugs")
router.register("drug-variants", DrugVariantViewSet, basename="drug-variants")
router.register("diagnoses", DiagnosisViewSet, basename="diagnoses")
router.register("medications", MedicationViewSet, basename="medications")
router.register("patient/unsafe-medications", PatientUnsafeMedicationViewSet, basename="patient-unsafe-medications")
router.register("doctor/unsafe-medications", DoctorUnsafeMedicationViewSet, basename="doctor-unsafe-medications")

urlpatterns = router.urls
