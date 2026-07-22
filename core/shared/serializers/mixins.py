from __future__ import annotations

from typing import Any

from rest_framework import serializers


class SerializerAuditMixin(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class SerializerOwnerMixin(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    def create(self, validated_data: dict[str, Any]) -> object:
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class SerializerTenantMixin(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    def create(self, validated_data: dict[str, Any]) -> object:
        validated_data["tenant"] = self.context["request"].user
        return super().create(validated_data)


__all__ = [
    "SerializerAuditMixin",
    "SerializerOwnerMixin",
    "SerializerTenantMixin",
]
