from __future__ import annotations

from unittest.mock import patch

from rest_framework import serializers

from core.shared.serializers.mixins import (
    SerializerAuditMixin,
    SerializerOwnerMixin,
    SerializerTenantMixin,
)


class DummyModel:
    class Meta:
        fields = []

    def save(self) -> None:
        pass


class AuditSerializer(SerializerAuditMixin):
    class Meta:
        model = DummyModel
        fields = ["created_at", "updated_at"]


class OwnerSerializer(SerializerOwnerMixin):
    class Meta:
        model = DummyModel
        fields = ["owner"]

    def create(self, validated_data):
        return super().create(validated_data)


class TenantSerializer(SerializerTenantMixin):
    class Meta:
        model = DummyModel
        fields = ["tenant"]

    def create(self, validated_data):
        return super().create(validated_data)


class TestSerializerAuditMixin:
    def test_declares_read_only_fields(self):
        assert "created_at" in SerializerAuditMixin._declared_fields
        assert "updated_at" in SerializerAuditMixin._declared_fields


class TestSerializerOwnerMixin:
    def test_set_owner_from_context(self):
        request = type("Request", (), {"user": "owner_user"})()
        serializer = OwnerSerializer(context={"request": request})

        captured = {}

        def mock_create(self_instance, validated_data):
            captured.update(validated_data)
            return DummyModel()

        with patch.object(serializers.ModelSerializer, "create", mock_create):
            serializer.create(validated_data={})

        assert captured.get("owner") == "owner_user"


class TestSerializerTenantMixin:
    def test_set_tenant_from_context(self):
        request = type("Request", (), {"user": "tenant_user"})()
        serializer = TenantSerializer(context={"request": request})

        captured = {}

        def mock_create(self_instance, validated_data):
            captured.update(validated_data)
            return DummyModel()

        with patch.object(serializers.ModelSerializer, "create", mock_create):
            serializer.create(validated_data={})

        assert captured.get("tenant") == "tenant_user"
