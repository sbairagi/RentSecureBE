from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (UnitViewSet, CaretakerViewSet, RenterViewSet, RentRecordViewSet, 
                    RentAgreementDraftViewSet, BuildingViewSet,
                    UnitImageViewSet, UnitDocumentViewSet)

router = DefaultRouter()
# Active end-point
router.register(r'buildings', BuildingViewSet, basename='buildings')
router.register(r'properties', UnitViewSet, basename='properties')
router.register(r'caretakers', CaretakerViewSet, basename='caretakers')
router.register(r'renters', RenterViewSet, basename='renters')
router.register(r'rent-records', RentRecordViewSet, basename='rent-records')


# De-prioritized for now do not touch bellow end-point
router.register(r'unit-images', UnitImageViewSet, basename='unit-images')
router.register(r'rent-agreements', RentAgreementDraftViewSet, basename='rent-agreements')
router.register(r'unit-all-documents', UnitDocumentViewSet, basename='unit-all-documents')

urlpatterns = [
    path('', include(router.urls)),
]


