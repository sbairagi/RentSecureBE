from __future__ import annotations

from core.infrastructure.enums import IntEnum, StringEnum


class TestInfrastructureEnums:
    def test_string_enum_creation(self):
        class Color(StringEnum):
            RED = "red"
            GREEN = "green"
            BLUE = "blue"

        assert Color.RED == "red"
        assert Color.GREEN.value == "green"

    def test_int_enum_creation(self):
        class Priority(IntEnum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3

        assert Priority.LOW == 1
        assert Priority.HIGH.value == 3

    def test_string_enum_membership(self):
        class Status(StringEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        assert "active" in Status._value2member_map_
        assert Status("active") == Status.ACTIVE

    def test_int_enum_membership(self):
        class Level(IntEnum):
            ONE = 1
            TWO = 2

        assert Level(1) == Level.ONE
