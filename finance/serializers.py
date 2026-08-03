from rest_framework import serializers

from .models import CAConnectionRequest, CAProfile, TaxSubmissionToCA


class CAConnectionRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    ca_name = serializers.CharField(source="ca_partner.name", read_only=True)

    class Meta:
        model = CAConnectionRequest
        fields = ["id", "user_email", "ca_name", "requested_at", "status", "notes"]


class CAProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAProfile
        fields = "__all__"
        read_only_fields = ("user",)


class TaxSubmissionToCASerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSubmissionToCA
        fields = "__all__"
        read_only_fields = ("user", "sent_at")
