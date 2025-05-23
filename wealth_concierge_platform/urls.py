from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, CaretakerViewSet, RenterViewSet, RentRecordViewSet

router = DefaultRouter()
router.register(r'properties', PropertyViewSet)
router.register(r'caretakers', CaretakerViewSet)
router.register(r'renters', RenterViewSet)
router.register(r'rent-records', RentRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]