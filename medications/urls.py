from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register("drugs", DrugViewSet, basename="drugs")
router.register("drug-variants", DrugVariantViewSet, basename="drug-variants")
router.register("diagnoses", DiagnosisViewSet, basename="diagnoses")
router.register("doctor/medications", DoctorMedicationViewSet,basename="doctor_medications")
router.register("patient/medications", PatientMedicationViewSet,basename="patient_medications")
router.register("patient/unsafe-medications", PatientUnsafeMedicationViewSet, basename="patient-unsafe-medications")
router.register("doctor/unsafe-medications", DoctorUnsafeMedicationViewSet, basename="doctor-unsafe-medications")

urlpatterns = router.urls
