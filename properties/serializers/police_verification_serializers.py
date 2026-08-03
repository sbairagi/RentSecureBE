from __future__ import annotations

from rest_framework import serializers

from ..models import PoliceVerification


class PoliceVerificationSerializer(serializers.ModelSerializer[PoliceVerification]):
    class Meta:
        model = PoliceVerification
        fields = "__all__"
        read_only_fields = ["id", "generated_at"]
