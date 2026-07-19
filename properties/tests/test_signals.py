import logging
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings
from django.utils import timezone

from notification.models import Notification
from properties.models import (
    ArchivedRenter,
    Caretaker,
    Renter,
    RentRecord,
    Unit,
    UnitDocument,
    UnitImage,
)
from properties.signals import (
    _archive_renter_if_needed,
    _generate_final_invoice_if_needed,
    _is_onboarding_update,
    generate_final_invoice_on_exit,
    handle_rent_payment,
    notify_owner_if_unit_vacant,
    update_renter_defaulter_status,
)

User = get_user_model()

from conftest import (  # noqa: E402
    BuildingFactory,
    RenterFactory,
    RentRecordFactory,
    UnitFactory,
    UserFactory,
)


@pytest.fixture
def owner(db):
    return UserFactory()


@pytest.fixture
def building(owner):
    return BuildingFactory(owner=owner)


@pytest.fixture
def unit(building):
    return UnitFactory(owner=building.owner, building=building)


@pytest.fixture
def unit_with_no_active_renter(unit):
    unit.last_vacated_at = None
    unit.save(update_fields=["last_vacated_at"])
    return unit


# ---------------------------------------------------------------------------
# 1. update_last_vacated_date_on_renter_exit
# ---------------------------------------------------------------------------


class TestUpdateLastVacatedDateOnRenterExit:
    def test_notice_period_with_other_active_renter_no_update(self, unit):
        RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        RenterFactory(unit=unit, status=Renter.RenterStatus.NOTICE_PERIOD)
        unit.refresh_from_db()
        assert unit.last_vacated_at is None

    def test_revoked_with_other_active_renter_no_update(self, unit):
        RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        RenterFactory(unit=unit, status=Renter.RenterStatus.REVOKED)
        unit.refresh_from_db()
        assert unit.last_vacated_at is None

    def test_deactivated_with_other_active_renter_no_update(self, unit):
        RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        RenterFactory(unit=unit, status=Renter.RenterStatus.DEACTIVATED)
        unit.refresh_from_db()
        assert unit.last_vacated_at is None

    def test_notice_period_no_active_renter_date_already_today_no_update(
        self, unit_with_no_active_renter
    ):
        today = timezone.now().date()
        unit_with_no_active_renter.last_vacated_at = today
        unit_with_no_active_renter.save(update_fields=["last_vacated_at"])
        RenterFactory(
            unit=unit_with_no_active_renter, status=Renter.RenterStatus.NOTICE_PERIOD
        )
        unit_with_no_active_renter.refresh_from_db()
        assert unit_with_no_active_renter.last_vacated_at == today

    def test_deactivated_no_active_renter_date_not_set_updates(
        self, unit_with_no_active_renter
    ):
        RenterFactory(
            unit=unit_with_no_active_renter, status=Renter.RenterStatus.DEACTIVATED
        )
        unit_with_no_active_renter.refresh_from_db()
        assert unit_with_no_active_renter.last_vacated_at == timezone.now().date()

    def test_revoked_no_active_renter_date_not_set_updates(
        self, unit_with_no_active_renter
    ):
        RenterFactory(
            unit=unit_with_no_active_renter, status=Renter.RenterStatus.REVOKED
        )
        unit_with_no_active_renter.refresh_from_db()
        assert unit_with_no_active_renter.last_vacated_at == timezone.now().date()


# ---------------------------------------------------------------------------
# 2. generate_renter_onboarding_token
# ---------------------------------------------------------------------------


class TestGenerateRenterOnboardingToken:
    def test_new_renter_without_token_generates_token(self, unit):
        renter = RenterFactory(unit=unit, onboarding_token="")
        assert renter.onboarding_token != ""

    def test_renter_with_existing_token_no_new_token(self, unit):
        existing_token = "existing-token-abc-123"
        renter = RenterFactory(unit=unit, onboarding_token=existing_token)
        assert renter.onboarding_token == existing_token


# ---------------------------------------------------------------------------
# 3. update_unit_status_on_renter_save
# ---------------------------------------------------------------------------


class TestUpdateUnitStatusOnRenterSave:
    def test_new_renter_created_unit_becomes_occupied(self, unit):
        RenterFactory(unit=unit)
        unit.refresh_from_db()
        assert unit.status == Unit.VacancyStatus.OCCUPIED
        assert unit.is_vacant is False

    def test_renter_deactivated_unit_becomes_vacant(self, unit):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        unit.refresh_from_db()
        assert unit.status == Unit.VacancyStatus.OCCUPIED

        renter.status = Renter.RenterStatus.DEACTIVATED
        renter.save(update_fields=["status"])
        unit.refresh_from_db()
        assert unit.status == Unit.VacancyStatus.VACANT
        assert unit.is_vacant is True


# ---------------------------------------------------------------------------
# 4. update_unit_status_on_renter_delete
# ---------------------------------------------------------------------------


class TestUpdateUnitStatusOnRenterDelete:
    def test_renter_deleted_unit_becomes_vacant(self, unit):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        unit.refresh_from_db()
        assert unit.status == Unit.VacancyStatus.OCCUPIED

        renter.delete()
        unit.refresh_from_db()
        assert unit.status == Unit.VacancyStatus.VACANT


# ---------------------------------------------------------------------------
# 5. update_building_usage
# ---------------------------------------------------------------------------


class TestUpdateBuildingUsage:
    def test_post_save_building_updates_usage(self, owner):
        BuildingFactory(owner=owner)
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(user=owner, feature_key="max_buildings").first()
        assert ul is not None
        assert ul.usage_count >= 1

    def test_post_delete_building_updates_usage(self, owner):
        building = BuildingFactory(owner=owner)
        building.delete()
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(user=owner, feature_key="max_buildings").first()
        assert ul is not None


# ---------------------------------------------------------------------------
# 6. update_unit_usage
# ---------------------------------------------------------------------------


class TestUpdateUnitUsage:
    def test_post_save_unit_updates_usage(self, building):
        UnitFactory(owner=building.owner, building=building)
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=building.owner, feature_key="max_units"
        ).first()
        assert ul is not None

    def test_post_delete_unit_updates_usage(self, building):
        unit = UnitFactory(owner=building.owner, building=building)
        unit.delete()
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=building.owner, feature_key="max_units"
        ).first()
        assert ul is not None


# ---------------------------------------------------------------------------
# 7. update_caretaker_usage
# ---------------------------------------------------------------------------


class TestUpdateCaretakerUsage:
    def test_post_save_caretaker_updates_usage(self, unit):
        Caretaker.objects.create(
            unit=unit,
            name="CT Test",
            phone="+919999999999",
            email="ct@test.com",
            joining_date=date.today(),
        )
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_caretakers"
        ).first()
        assert ul is not None

    def test_post_delete_caretaker_updates_usage(self, unit):
        caretaker = Caretaker.objects.create(
            unit=unit,
            name="CT Test",
            phone="+919999999999",
            email="ct@test.com",
            joining_date=date.today(),
        )
        caretaker.delete()
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_caretakers"
        ).first()
        assert ul is not None


# ---------------------------------------------------------------------------
# 8. update_renter_usage
# ---------------------------------------------------------------------------


class TestUpdateRenterUsage:
    def test_post_save_renter_updates_usage(self, unit):
        RenterFactory(unit=unit)
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_renters"
        ).first()
        assert ul is not None

    def test_post_delete_renter_updates_usage(self, unit):
        renter = RenterFactory(unit=unit)
        renter.delete()
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_renters"
        ).first()
        assert ul is not None


# ---------------------------------------------------------------------------
# 9. update_unit_images_usage
# ---------------------------------------------------------------------------


class TestUpdateUnitImagesUsage:
    def test_post_save_unit_image_updates_usage(self, unit):
        image_file = ContentFile(b"fake-image-content", name="test.jpg")
        UnitImage.objects.create(unit=unit, image=image_file)
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_unit_images"
        ).first()
        assert ul is not None

    def test_post_delete_unit_image_updates_usage(self, unit):
        image_file = ContentFile(b"fake-image-content", name="test.jpg")
        unit_image = UnitImage.objects.create(unit=unit, image=image_file)
        unit_image.delete()
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_unit_images"
        ).first()
        assert ul is not None


# ---------------------------------------------------------------------------
# 10. update_unit_documents_usage
# ---------------------------------------------------------------------------


class TestUpdateUnitDocumentsUsage:
    def test_post_save_unit_document_updates_usage(self, unit):
        doc_file = ContentFile(b"fake-doc-content", name="test.pdf")
        UnitDocument.objects.create(unit=unit, document=doc_file)
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_unit_images"
        ).first()
        assert ul is not None

    def test_post_delete_unit_document_updates_usage(self, unit):
        doc_file = ContentFile(b"fake-doc-content", name="test.pdf")
        unit_doc = UnitDocument.objects.create(unit=unit, document=doc_file)
        unit_doc.delete()
        from core.models import UsageLimit

        ul = UsageLimit.objects.filter(
            user=unit.owner, feature_key="max_unit_images"
        ).first()
        assert ul is not None


# ---------------------------------------------------------------------------
# 11. handle_rent_payment
# ---------------------------------------------------------------------------


class TestHandleRentPayment:
    @patch("properties.services.receipt_service.send_rent_receipt_on_payment")
    @patch("notification.services.voice_note_service.send_thank_you_voice_note")
    @patch("properties.signals.cancel_reminder_job")
    def test_paid_status_triggers_voice_note_cancel_and_receipt(
        self, mock_cancel, mock_voice, mock_receipt, unit
    ):
        user = UserFactory()
        renter = RenterFactory(unit=unit, user=user, status=Renter.RenterStatus.ACTIVE)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PENDING,
            due_date=timezone.now().date() + timedelta(days=5),
        )
        rent.status = RentRecord.Status.PAID
        handle_rent_payment(sender=RentRecord, instance=rent)
        mock_cancel.assert_called_once_with(f"rent_{rent.id}")
        mock_voice.assert_called_once_with(rent)
        mock_receipt.assert_called_once_with(rent)
        assert Notification.objects.filter(user=renter.user).exists()

    @patch("properties.services.receipt_service.send_rent_receipt_on_payment")
    @patch("notification.services.voice_note_service.send_thank_you_voice_note")
    @patch("properties.signals.cancel_reminder_job")
    def test_paid_status_no_renter_user_skips_notification(
        self, mock_cancel, mock_voice, mock_receipt, unit
    ):
        renter = RenterFactory(unit=unit, user=None)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PAID,
            due_date=timezone.now().date() - timedelta(days=1),
        )
        handle_rent_payment(sender=RentRecord, instance=rent)
        assert not Notification.objects.filter(user__isnull=True).exists()

    @patch("properties.services.receipt_service.send_rent_receipt_on_payment")
    @patch("notification.services.voice_note_service.send_thank_you_voice_note")
    @patch("properties.signals.cancel_reminder_job")
    def test_pending_status_skips_all_external_calls(
        self, mock_cancel, mock_voice, mock_receipt, unit
    ):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PENDING,
            due_date=timezone.now().date() + timedelta(days=5),
        )
        handle_rent_payment(sender=RentRecord, instance=rent)
        mock_cancel.assert_not_called()
        mock_voice.assert_not_called()
        mock_receipt.assert_not_called()

    @patch(
        "properties.services.receipt_service.send_rent_receipt_on_payment",
        side_effect=Exception("SMTP down"),
    )
    @patch("notification.services.voice_note_service.send_thank_you_voice_note")
    @patch("properties.signals.cancel_reminder_job")
    def test_paid_status_receipt_exception_logged(
        self, mock_cancel, mock_voice, mock_receipt, unit, caplog
    ):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PAID,
            due_date=timezone.now().date() - timedelta(days=1),
        )
        with caplog.at_level(logging.ERROR):
            handle_rent_payment(sender=RentRecord, instance=rent)
        assert "Failed to send receipt email" in caplog.text


# ---------------------------------------------------------------------------
# 12. update_renter_defaulter_status
# ---------------------------------------------------------------------------


class TestUpdateRenterDefaulterStatus:
    @patch("notification.services.rent_notify_service.notify_owner_renter_flagged")
    def test_pending_past_due_missed_rents_incremented_and_flagged(
        self, mock_notify, unit
    ):
        renter = RenterFactory(unit=unit, missed_rents=2, is_flagged=False)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PENDING,
            due_date=timezone.now().date() - timedelta(days=5),
        )
        update_renter_defaulter_status(rent)
        renter.refresh_from_db()
        assert renter.missed_rents == 3
        assert renter.is_flagged is True
        assert renter.flagged_reason == "Missed 3 or more rent payments."
        mock_notify.assert_called_once_with(renter)

    @patch("notification.services.rent_notify_service.notify_owner_renter_flagged")
    def test_pending_past_due_already_flagged_no_notify(self, mock_notify, unit):
        renter = RenterFactory(
            unit=unit, missed_rents=5, is_flagged=True, flagged_reason="Already flagged"
        )
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PENDING,
            due_date=timezone.now().date() - timedelta(days=5),
        )
        update_renter_defaulter_status(rent)
        renter.refresh_from_db()
        assert renter.missed_rents == 6
        assert renter.is_flagged is True
        mock_notify.assert_not_called()

    def test_not_pending_returns_early(self, unit):
        renter = RenterFactory(unit=unit, missed_rents=0)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PAID,
            due_date=timezone.now().date() + timedelta(days=5),
        )
        original_missed = renter.missed_rents
        update_renter_defaulter_status(rent)
        renter.refresh_from_db()
        assert renter.missed_rents == original_missed

    def test_pending_not_past_due_returns_early(self, unit):
        renter = RenterFactory(unit=unit, missed_rents=0)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PENDING,
            due_date=timezone.now().date() + timedelta(days=5),
        )
        original_missed = renter.missed_rents
        update_renter_defaulter_status(rent)
        renter.refresh_from_db()
        assert renter.missed_rents == original_missed

    def test_pending_past_due_renter_none_returns_early(self, unit):
        rent = RentRecordFactory(
            unit=unit,
            renter=None,
            status=RentRecord.Status.PENDING,
            due_date=timezone.now().date() - timedelta(days=5),
        )
        update_renter_defaulter_status(rent)

    @patch(
        "notification.services.rent_notify_service.notify_owner_renter_flagged",
        side_effect=Exception("Notify failed"),
    )
    def test_notify_exception_logged_and_continues(self, mock_notify, unit, caplog):
        renter = RenterFactory(unit=unit, missed_rents=2, is_flagged=False)
        rent = RentRecordFactory(
            unit=unit,
            renter=renter,
            status=RentRecord.Status.PENDING,
            due_date=timezone.now().date() - timedelta(days=5),
        )
        with caplog.at_level(logging.WARNING):
            update_renter_defaulter_status(rent)
        renter.refresh_from_db()
        assert renter.is_flagged is True
        assert "Failed to notify owner" in caplog.text


# ---------------------------------------------------------------------------
# 13. notify_owner_if_unit_vacant
# ---------------------------------------------------------------------------


class TestNotifyOwnerIfUnitVacant:
    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    def test_deactivated_no_other_active_with_whatsapp_sends_message(
        self, mock_client, unit
    ):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.DEACTIVATED)
        mock_client.return_value.messages.create.return_value = MagicMock()
        mock_client.reset_mock()
        notify_owner_if_unit_vacant(sender=Renter, instance=renter)
        mock_client.return_value.messages.create.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    def test_revoked_no_other_active_with_whatsapp_sends_message(
        self, mock_client, unit
    ):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.REVOKED)
        mock_client.return_value.messages.create.return_value = MagicMock()
        mock_client.reset_mock()
        notify_owner_if_unit_vacant(sender=Renter, instance=renter)
        mock_client.return_value.messages.create.assert_called_once()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    def test_deactivated_no_other_active_no_whatsapp_number_skips(
        self, mock_client, unit, owner
    ):
        owner.whatsapp_number = ""
        owner.save(update_fields=["whatsapp_number"])
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.DEACTIVATED)
        notify_owner_if_unit_vacant(sender=Renter, instance=renter)
        mock_client.return_value.messages.create.assert_not_called()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    def test_deactivated_other_active_renters_exist_skips(self, mock_client, unit):
        RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        deactivated_renter = RenterFactory(
            unit=unit, status=Renter.RenterStatus.DEACTIVATED
        )
        notify_owner_if_unit_vacant(sender=Renter, instance=deactivated_renter)
        mock_client.return_value.messages.create.assert_not_called()

    @override_settings(ENABLE_WHATSAPP=True)
    @patch("notification.adapters.whatsapp.Client")
    def test_active_status_skips(self, mock_client, unit):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        notify_owner_if_unit_vacant(sender=Renter, instance=renter)
        mock_client.return_value.messages.create.assert_not_called()


# ---------------------------------------------------------------------------
# 14. generate_final_invoice_on_exit
# ---------------------------------------------------------------------------


class TestGenerateFinalInvoiceOnExit:
    @patch("properties.signals._generate_final_invoice_if_needed")
    @patch("properties.signals._archive_renter_if_needed")
    def test_onboarding_update_returns_early(self, mock_archive, mock_invoice, unit):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        mock_invoice.reset_mock()
        mock_archive.reset_mock()
        generate_final_invoice_on_exit(
            sender=Renter,
            instance=renter,
            update_fields=["onboarding_token"],
        )
        mock_invoice.assert_not_called()
        mock_archive.assert_not_called()

    @patch("properties.signals._generate_final_invoice_if_needed")
    @patch("properties.signals._archive_renter_if_needed")
    def test_active_status_returns_early(self, mock_archive, mock_invoice, unit):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        mock_invoice.reset_mock()
        mock_archive.reset_mock()
        generate_final_invoice_on_exit(
            sender=Renter, instance=renter, update_fields=None
        )
        mock_invoice.assert_not_called()
        mock_archive.assert_not_called()

    @patch("properties.signals._generate_final_invoice_if_needed")
    @patch("properties.signals._archive_renter_if_needed")
    def test_notice_period_generates_invoice_no_archive(
        self, mock_archive, mock_invoice, unit
    ):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.NOTICE_PERIOD)
        mock_invoice.reset_mock()
        mock_archive.reset_mock()
        generate_final_invoice_on_exit(
            sender=Renter, instance=renter, update_fields=None
        )
        mock_invoice.assert_called_once_with(renter)
        mock_archive.assert_not_called()

    @patch("properties.signals._generate_final_invoice_if_needed")
    @patch("properties.signals._archive_renter_if_needed")
    def test_deactivated_generates_invoice_and_archives(
        self, mock_archive, mock_invoice, unit
    ):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.DEACTIVATED)
        mock_invoice.reset_mock()
        mock_archive.reset_mock()
        generate_final_invoice_on_exit(
            sender=Renter, instance=renter, update_fields=None
        )
        mock_invoice.assert_called_once_with(renter)
        mock_archive.assert_called_once_with(renter)

    @patch("properties.signals._generate_final_invoice_if_needed")
    @patch("properties.signals._archive_renter_if_needed")
    def test_revoked_generates_invoice_and_archives(
        self, mock_archive, mock_invoice, unit
    ):
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.REVOKED)
        mock_invoice.reset_mock()
        mock_archive.reset_mock()
        generate_final_invoice_on_exit(
            sender=Renter, instance=renter, update_fields=None
        )
        mock_invoice.assert_called_once_with(renter)
        mock_archive.assert_called_once_with(renter)


# ---------------------------------------------------------------------------
# 15. _generate_final_invoice_if_needed
# ---------------------------------------------------------------------------


class TestGenerateFinalInvoiceIfNeeded:
    @patch("properties.signals.renter_exited.send")
    def test_rent_record_exists_signal_sent(self, mock_signal, unit):
        renter = RenterFactory(unit=unit)
        RentRecordFactory(unit=unit, renter=renter)
        _generate_final_invoice_if_needed(renter)
        mock_signal.assert_called_once()

    def test_no_rent_record_returns_early(self, unit):
        renter = RenterFactory(unit=unit)
        _generate_final_invoice_if_needed(renter)


# ---------------------------------------------------------------------------
# 16. _archive_renter_if_needed
# ---------------------------------------------------------------------------


class TestArchiveRenterIfNeeded:
    @patch("properties.signals.renter_archived.send")
    def test_already_archived_returns_early(self, mock_signal, unit):
        renter = RenterFactory(unit=unit)
        ArchivedRenter.objects.create(
            renter=renter,
            data={},
            agreement_pdf="archived/agreements/test.pdf",
            police_pdf="archived/police/test.pdf",
            final_invoice="archived/final_invoice/test.pdf",
        )
        _archive_renter_if_needed(renter)
        mock_signal.assert_not_called()

    @patch("properties.signals.renter_archived.send")
    def test_not_archived_sends_signal(self, mock_signal, unit):
        renter = RenterFactory(unit=unit)
        _archive_renter_if_needed(renter)
        mock_signal.assert_called_once()


# ---------------------------------------------------------------------------
# 17. _is_onboarding_update
# ---------------------------------------------------------------------------


class TestIsOnboardingUpdate:
    def test_none_update_fields_returns_false(self):
        assert _is_onboarding_update(None) is False

    def test_onboarding_token_only_returns_true(self):
        assert _is_onboarding_update(["onboarding_token"]) is True

    def test_onboarding_link_sent_at_only_returns_true(self):
        assert _is_onboarding_update(["onboarding_link_sent_at"]) is True

    def test_both_onboarding_fields_returns_true(self):
        assert (
            _is_onboarding_update(["onboarding_token", "onboarding_link_sent_at"])
            is True
        )

    def test_non_onboarding_field_returns_false(self):
        assert _is_onboarding_update(["name"]) is False

    def test_mixed_fields_returns_false(self):
        assert _is_onboarding_update(["onboarding_token", "name"]) is False
