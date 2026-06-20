import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache


class _FakeMessage:
    sid = "SM_TEST"


class _FakeMessages:
    def create(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return _FakeMessage()


class _FakeTwilioClient:
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.messages = _FakeMessages()


@pytest.fixture(autouse=True)
def rentsecure_test_defaults(db, monkeypatch):  # type: ignore[no-untyped-def]
    cache.clear()
    Group.objects.get_or_create(name="tenant")
    Group.objects.get_or_create(name="renter")

    monkeypatch.setattr("core.views.Client", _FakeTwilioClient)
    monkeypatch.setattr("notification.utils.Client", _FakeTwilioClient)
    monkeypatch.setattr(
        "notification.services.whatsapp_service.Client", _FakeTwilioClient
    )
    monkeypatch.setattr(
        "properties.views.rent_record_views.create_payment_link",
        lambda rent: f"https://payments.test/rent/{rent.id}",
    )
    monkeypatch.setattr(
        "properties.signals.send_thank_you_voice_note", lambda rent: None
    )
    yield
