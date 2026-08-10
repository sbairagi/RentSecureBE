from rest_framework import serializers


class ErrorPayloadSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False, default=dict)
    request_id = serializers.CharField(required=False, allow_blank=True)


class ErrorEnvelopeSerializer(serializers.Serializer):
    error = ErrorPayloadSerializer()


class ValidationErrorDetailSerializer(serializers.Serializer):
    field = serializers.CharField()
    messages = serializers.ListField(child=serializers.CharField())
