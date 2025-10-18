from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SharedAccessViewSet

router = DefaultRouter()
router.register(r'shared-access', SharedAccessViewSet, basename='shared-access')

urlpatterns = [
    path('', include(router.urls)),
]