from __future__ import annotations

import uuid

import pytest

from core.shared.ids import new_uuid, parse_uuid, validate_uuid


class TestSharedIds:
    def test_new_uuid_returns_valid_string(self):
        uid = new_uuid()
        assert isinstance(uid, str)
        uuid.UUID(uid)

    def test_new_uuid_unique(self):
        ids = {new_uuid() for _ in range(100)}
        assert len(ids) == 100

    def test_parse_uuid_valid(self):
        uid_str = str(uuid.uuid4())
        result = parse_uuid(uid_str)
        assert isinstance(result, uuid.UUID)
        assert str(result) == uid_str

    def test_parse_uuid_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid UUID"):
            parse_uuid("not-a-uuid")

    def test_validate_uuid_valid(self):
        uid_str = str(uuid.uuid4())
        assert validate_uuid(uid_str) is True

    def test_validate_uuid_invalid(self):
        assert validate_uuid("not-a-uuid") is False
        assert validate_uuid("") is False

    def test_parse_uuid_normalizes(self):
        result = parse_uuid("12345678-1234-5678-1234-567812345678")
        assert result.hex == "12345678123456781234567812345678"
