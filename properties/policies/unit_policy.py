"""Unit Policy Module.

Centralizes authorization and ownership rules for units.
Policies are pure decision functions with no side effects.
"""

from __future__ import annotations

from typing import Any, cast


class UnitPolicy:
    """Policy rules for unit access and modification."""

    @staticmethod
    def can_access_unit(unit: Any, user: Any) -> bool:
        """Return True if the user can access the unit."""
        if unit is None:
            return False
        return cast(bool, unit.owner == user)
