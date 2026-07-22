from __future__ import annotations

from typing import Any

from core.shared.repositories.base import IRepository


class FakeEntity:
    def __init__(self, id_val: int, name: str) -> None:
        self.id = id_val
        self.name = name


class FakeRepo(IRepository[FakeEntity]):
    def __init__(self) -> None:
        self._store: dict[int, FakeEntity] = {
            1: FakeEntity(1, "one"),
            2: FakeEntity(2, "two"),
        }

    def get(self, id: Any) -> FakeEntity | None:
        return self._store.get(id)

    def list(self, **filters: Any) -> list[FakeEntity]:
        return list(self._store.values())

    def add(self, entity: FakeEntity) -> FakeEntity:
        self._store[entity.id] = entity
        return entity

    def remove(self, entity: FakeEntity) -> None:
        del self._store[entity.id]


class TestIRepository:
    def test_get_existing(self):
        repo = FakeRepo()
        entity = repo.get(1)
        assert entity is not None
        assert entity.name == "one"

    def test_get_missing_returns_none(self):
        repo = FakeRepo()
        assert repo.get(999) is None

    def test_list_returns_all(self):
        repo = FakeRepo()
        items = repo.list()
        assert len(items) == 2

    def test_add_new(self):
        repo = FakeRepo()
        entity = FakeEntity(3, "three")
        result = repo.add(entity)
        assert result is entity
        assert repo.get(3) is entity

    def test_remove(self):
        repo = FakeRepo()
        repo.remove(repo.get(1))
        assert repo.get(1) is None
