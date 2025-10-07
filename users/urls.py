from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

router = DefaultRouter()
#endpoints reservados para administradores
router.register(r'all', UserViewSet)
router.register(r'patients', PatientProfileViewSet)
router.register(r'families', FamilyProfileViewSet)
router.register(r'doctors', DoctorProfileViewSet)

urlpatterns = [
    #incluimos los endpints para administradores en urlpatterns
    path('', include(router.urls)),
    #Endpoints para uso de los usuarios no administradores
#   path("patients/<int:patient_id>/detail/", PatientDetailForFamily.as_view(), name="patient-detail-for-family"),
#   path("doctor/patients/<int:patient_id>/detail/", PatientDetailForDoctor.as_view(), name="doctor-patient-detail"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify"),
]
