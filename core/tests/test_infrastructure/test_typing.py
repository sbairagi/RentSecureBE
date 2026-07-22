from __future__ import annotations

from core.infrastructure import typing as core_typing


class TestInfrastructureTyping:
    def test_type_var_defined(self):
        assert hasattr(core_typing, "T")

    def test_co_variant_defined(self):
        assert hasattr(core_typing, "T_co")

    def test_contra_variant_defined(self):
        assert hasattr(core_typing, "T_contra")
