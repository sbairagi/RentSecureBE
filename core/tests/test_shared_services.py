from __future__ import annotations

from core.shared.services.base import DomainService


class ConcreteService(DomainService):
    def do_work(self) -> str:
        return "done"


class TestDomainService:
    def test_marker_class_instantiable(self):
        svc = DomainService()
        assert svc is not None

    def test_concrete_subclass(self):
        svc = ConcreteService()
        assert svc.do_work() == "done"
