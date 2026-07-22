from __future__ import annotations

from core.shared.pagination import PageRequest, PageResponse


class Item:
    def __init__(self, id_val: int) -> None:
        self.id = id_val


class TestPageRequest:
    def test_default_values(self):
        req = PageRequest[Item]()
        assert req.page == 1
        assert req.page_size == 20
        assert req.filters == {}

    def test_custom_values(self):
        req = PageRequest(page=2, page_size=50, filters={"name": "x"})
        assert req.page == 2
        assert req.page_size == 50
        assert req.filters == {"name": "x"}

    def test_page_clamped_to_minimum(self):
        req = PageRequest(page=0)
        assert req.page == 1

    def test_page_size_clamped_to_minimum(self):
        req = PageRequest(page_size=0)
        assert req.page_size == 1

    def test_page_size_clamped_to_maximum(self):
        req = PageRequest(page_size=200)
        assert req.page_size == 100


class TestPageResponse:
    def test_total_pages_empty(self):
        resp = PageResponse(items=[], total=0, page=1, page_size=20)
        assert resp.total_pages == 0

    def test_total_pages_single(self):
        resp = PageResponse(items=list(range(10)), total=10, page=1, page_size=20)
        assert resp.total_pages == 1

    def test_total_pages_multiple(self):
        resp = PageResponse(items=list(range(10)), total=25, page=1, page_size=10)
        assert resp.total_pages == 3

    def test_has_next_true(self):
        resp = PageResponse(items=list(range(10)), total=25, page=1, page_size=10)
        assert resp.has_next is True

    def test_has_next_false(self):
        resp = PageResponse(items=list(range(10)), total=15, page=2, page_size=10)
        assert resp.has_next is False

    def test_has_previous_true(self):
        resp = PageResponse(items=list(range(10)), total=25, page=2, page_size=10)
        assert resp.has_previous is True

    def test_has_previous_false(self):
        resp = PageResponse(items=list(range(10)), total=25, page=1, page_size=10)
        assert resp.has_previous is False

    def test_rounding_up(self):
        resp = PageResponse(items=[], total=21, page=1, page_size=10)
        assert resp.total_pages == 3
