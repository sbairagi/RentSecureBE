from rest_framework import viewsets, permissions
from .models import Property, Caretaker, Renter, RentRecord
from .serializers import PropertySerializer, CaretakerSerializer, RenterSerializer, RentRecordSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Property.objects.all()
    serializer_class = PropertySerializer


class CaretakerViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Caretaker.objects.all()
    serializer_class = CaretakerSerializer


class RenterViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Renter.objects.all()
    serializer_class = RenterSerializer


class RentRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = RentRecord.objects.all()
    serializer_class = RentRecordSerializer