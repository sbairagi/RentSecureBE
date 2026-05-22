from rest_framework import serializers

from .models import CAProfile, TaxSubmissionToCA


class CAProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAProfile
        fields = '__all__'

class TaxSubmissionToCASerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxSubmissionToCA
        fields = '__all__'
        read_only_fields = ('sent_at',)
