from __future__ import annotations

import pytest

from core.infrastructure.ids import EntityId


class TestEntityId:
    def test_create_from_valid_uuid_string(self):
        eid = EntityId("12345678-1234-5678-1234-567812345678")
        assert eid.hex == "12345678123456781234567812345678"

    def test_create_from_invalid_string_raises(self):
        with pytest.raises(ValueError, match="Invalid entity ID"):
            EntityId.from_string("not-a-uuid")

    def test_from_string_returns_entity_id(self):
        eid = EntityId.from_string("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        assert isinstance(eid, EntityId)

    def test_str_representation(self):
        eid = EntityId("00000000-0000-0000-0000-000000000000")
        assert str(eid) == "00000000-0000-0000-0000-000000000000"

    def test_equality(self):
        eid1 = EntityId("12345678-1234-5678-1234-567812345678")
        eid2 = EntityId("12345678-1234-5678-1234-567812345678")
        assert eid1 == eid2

    def test_inequality(self):
        eid1 = EntityId("11111111-1111-1111-1111-111111111111")
        eid2 = EntityId("22222222-2222-2222-2222-222222222222")
        assert eid1 != eid2
