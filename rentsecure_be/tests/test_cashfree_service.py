"""Tests for rentsecure_be/services/cashfree_service.py."""

from unittest.mock import MagicMock, patch

import pytest

import rentsecure_be.services.cashfree_service as cashfree_service
from conftest import OwnerBankDetailsFactory, RenterFactory, RentRecordFactory
from core.models import OwnerBankDetails
from properties.models.rent_record_models import RentRecord as RentRecordModel
from rentsecure_be.services.cashfree_service import (
    _send_whatsapp_payout_alert,
    delete_beneficiary,
    pay_owner_after_rent,
    process_rent_payout,
    register_cashfree_beneficiary,
    register_owner_with_cashfree,
)


@pytest.fixture(autouse=True)
def _ensure_cashfree_rentrecord():
    cashfree_service.RentRecord = RentRecordModel
    yield
    cashfree_service.RentRecord = RentRecordModel


@pytest.fixture
def owner_bank_details(db):
    return OwnerBankDetailsFactory()


@pytest.fixture
def rent_record_with_renter(db, unit):
    renter = RenterFactory(unit=unit)
    return RentRecordFactory(unit=unit, renter=renter)


@pytest.mark.django_db
class TestRegisterOwnerWithCashfree:
    def test_type_error_for_non_owner_bank_details(self):
        with pytest.raises(
            TypeError, match="owner must be an OwnerBankDetails instance"
        ):
            register_owner_with_cashfree("not_an_instance")

    @patch("rentsecure_be.services.cashfree_service.add_beneficiary")
    def test_success_response_saves_bene_id(
        self, mock_add_beneficiary, owner, owner_bank_details
    ):
        mock_add_beneficiary.return_value = {
            "status": "SUCCESS",
            "data": {"beneId": "owner_1"},
        }
        register_owner_with_cashfree(owner_bank_details)
        owner_bank_details.refresh_from_db()
        assert owner_bank_details.beneficiary_id == "owner_1"
        assert owner_bank_details.bank_account_verified is True

    @patch("rentsecure_be.services.cashfree_service.add_beneficiary")
    def test_failed_response_does_not_save(
        self, mock_add_beneficiary, owner, owner_bank_details
    ):
        mock_add_beneficiary.return_value = {"status": "FAILED", "message": "error"}
        original_bene_id = owner_bank_details.beneficiary_id
        register_owner_with_cashfree(owner_bank_details)
        owner_bank_details.refresh_from_db()
        assert owner_bank_details.beneficiary_id == original_bene_id
        assert owner_bank_details.bank_account_verified is False


@pytest.mark.django_db
class TestPayOwnerAfterRent:
    @patch("notification.services.rent_notify_service.notify_owner")
    @patch("notification.services.rent_notify_service.notify_renter")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_already_success_payout_returns_already_paid(
        self,
        mock_make_payout,
        mock_notify_renter,
        mock_notify_owner,
        rent_record_with_renter,
    ):
        rent_record_with_renter.payout_status = "SUCCESS"
        rent_record_with_renter.save()
        result = pay_owner_after_rent(rent_record_with_renter)
        assert result["status"] == "ALREADY_PAID"
        mock_make_payout.assert_not_called()
        mock_notify_renter.assert_not_called()
        mock_notify_owner.assert_not_called()

    @patch("core.models.OwnerBankDetails")
    def test_no_renter_raises_value_error(self, mock_owner_bank_details_cls, unit):
        rent_record = RentRecordFactory(unit=unit, renter=None)
        with pytest.raises(ValueError, match="Owner not found for rent"):
            pay_owner_after_rent(rent_record)

    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_bank_details_not_found_raises_value_error(
        self, mock_make_payout, rent_record_with_renter
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.DoesNotExist = OwnerBankDetails.DoesNotExist
            mock_cls.objects.get.side_effect = OwnerBankDetails.DoesNotExist
            with pytest.raises(ValueError, match="Owner not registered with Cashfree"):
                pay_owner_after_rent(rent_record_with_renter)

    @patch("rentsecure_be.services.cashfree_service.make_payout")
    @patch("core.models.OwnerBankDetails")
    def test_no_beneficiary_id_raises_value_error(
        self,
        mock_owner_bank_details_cls,
        mock_make_payout,
        rent_record_with_renter,
        owner_bank_details,
    ):
        owner_bank_details.beneficiary_id = ""
        owner_bank_details.save()
        mock_owner_bank_details_cls.objects.get.return_value = owner_bank_details
        with pytest.raises(ValueError, match="Owner not registered with Cashfree"):
            pay_owner_after_rent(rent_record_with_renter)

    @patch("rentsecure_be.services.cashfree_service._send_whatsapp_payout_alert")
    @patch("notification.services.rent_notify_service.notify_owner")
    @patch("notification.services.rent_notify_service.notify_renter")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_success_payout_notifies(
        self,
        mock_make_payout,
        mock_notify_renter,
        mock_notify_owner,
        mock_send_whatsapp,
        rent_record_with_renter,
        owner,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.return_value = {"status": "SUCCESS"}
            pay_owner_after_rent(rent_record_with_renter)
            rent_record_with_renter.refresh_from_db()
            assert rent_record_with_renter.payout_status == "SUCCESS"
            mock_notify_renter.assert_called_once()
            mock_notify_owner.assert_called_once()
            mock_send_whatsapp.assert_called_once_with(rent_record_with_renter)

    @patch("rentsecure_be.services.cashfree_service._send_whatsapp_payout_alert")
    @patch("notification.services.rent_notify_service.notify_renter")
    @patch("notification.services.rent_notify_service.notify_owner")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_failed_payout_notifies_renter(
        self,
        mock_make_payout,
        mock_notify_owner,
        mock_notify_renter,
        mock_send_whatsapp,
        rent_record_with_renter,
        owner,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.return_value = {"status": "FAILED"}
            pay_owner_after_rent(rent_record_with_renter)
            rent_record_with_renter.refresh_from_db()
            assert rent_record_with_renter.payout_status == "FAILED"
            mock_notify_renter.assert_called_once()
            mock_notify_owner.assert_not_called()
            mock_send_whatsapp.assert_called_once_with(rent_record_with_renter)

    @patch("rentsecure_be.services.cashfree_service._send_whatsapp_payout_alert")
    @patch("notification.services.rent_notify_service.notify_owner")
    @patch("notification.services.rent_notify_service.notify_renter")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_success_payout_calls_whatsapp_alert(
        self,
        mock_make_payout,
        mock_notify_renter,
        mock_notify_owner,
        mock_send_whatsapp,
        rent_record_with_renter,
        owner,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.return_value = {"status": "SUCCESS"}
            pay_owner_after_rent(rent_record_with_renter)
            mock_send_whatsapp.assert_called_once_with(rent_record_with_renter)

    @patch("notification.services.rent_notify_service.send_payout_notification")
    def test_send_whatsapp_alert_without_whatsapp_number(
        self, mock_send_payout_notification
    ):
        owner = MagicMock()
        profile = MagicMock()
        profile.whatsapp_number = None
        renter = MagicMock()
        renter.unit.owner = owner
        rent_record = MagicMock()
        rent_record.renter = renter
        with patch.object(owner, "profile", profile):
            _send_whatsapp_payout_alert(rent_record)
        mock_send_payout_notification.assert_not_called()

    @patch("notification.services.rent_notify_service.send_payout_notification")
    def test_send_whatsapp_alert_with_whatsapp_number(
        self, mock_send_payout_notification
    ):
        profile = MagicMock()
        profile.whatsapp_number = "+919876543210"
        owner = MagicMock()
        owner.profile = profile
        renter = MagicMock()
        renter.unit.owner = owner
        rent_record = MagicMock()
        rent_record.renter = renter
        _send_whatsapp_payout_alert(rent_record)
        mock_send_payout_notification.assert_called_once_with(rent_record)

    @patch("notification.services.rent_notify_service.send_payout_notification")
    def test_send_whatsapp_alert_with_no_renter(self, mock_send_payout_notification):
        rent_record = MagicMock()
        rent_record.renter = None
        _send_whatsapp_payout_alert(rent_record)
        mock_send_payout_notification.assert_not_called()


@pytest.mark.django_db
class TestRegisterCashfreeBeneficiary:
    def test_type_error_for_non_owner_bank_details(self):
        with pytest.raises(
            TypeError, match="bank_details must be an OwnerBankDetails instance"
        ):
            register_cashfree_beneficiary("not_an_instance")

    @patch("rentsecure_be.services.cashfree_service.add_beneficiary")
    def test_success_response_saves_bene_id(
        self, mock_add_beneficiary, owner, owner_bank_details
    ):
        expected_bene_id = f"owner_{owner_bank_details.owner.id}"
        mock_add_beneficiary.return_value = {
            "status": "SUCCESS",
            "data": {"beneId": expected_bene_id},
        }
        result = register_cashfree_beneficiary(owner_bank_details)
        owner_bank_details.refresh_from_db()
        assert owner_bank_details.beneficiary_id == expected_bene_id
        assert owner_bank_details.bank_account_verified is True
        assert result["status"] == "SUCCESS"

    @patch("rentsecure_be.services.cashfree_service.add_beneficiary")
    def test_failed_response_does_not_save(
        self, mock_add_beneficiary, owner, owner_bank_details
    ):
        mock_add_beneficiary.return_value = {"status": "FAILED", "message": "error"}
        original_bene_id = owner_bank_details.beneficiary_id
        result = register_cashfree_beneficiary(owner_bank_details)
        owner_bank_details.refresh_from_db()
        assert owner_bank_details.beneficiary_id == original_bene_id
        assert result["status"] == "FAILED"


@pytest.mark.django_db
class TestProcessRentPayout:
    def test_type_error_for_non_rent_record(self):
        with pytest.raises(TypeError, match="rent must be a RentRecord instance"):
            process_rent_payout("not_an_instance")

    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_no_owner_returns_failed(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        unit,
    ):
        rent_record = RentRecordFactory(unit=unit, renter=None)
        result = process_rent_payout(rent_record)
        rent_record.refresh_from_db()
        assert rent_record.payout_status == "FAILED"
        assert result["status"] == "FAILED"
        assert "Owner not found for rent" in result["message"]
        mock_notify_owner_post_payout.assert_not_called()
        mock_send_payout_notification.assert_not_called()

    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_no_bank_details_returns_failed(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        rent_record_with_renter,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.DoesNotExist = OwnerBankDetails.DoesNotExist
            mock_cls.objects.get.side_effect = OwnerBankDetails.DoesNotExist
            result = process_rent_payout(rent_record_with_renter)
            rent_record_with_renter.refresh_from_db()
            assert rent_record_with_renter.payout_status == "FAILED"
            assert result["status"] == "FAILED"
            assert "Owner bank details not found" in result["message"]
            mock_make_payout.assert_not_called()
            mock_notify_owner_post_payout.assert_not_called()
            mock_send_payout_notification.assert_not_called()

    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_no_beneficiary_id_returns_failed(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        rent_record_with_renter,
        owner_bank_details,
    ):
        owner_bank_details.beneficiary_id = ""
        owner_bank_details.save()
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            result = process_rent_payout(rent_record_with_renter)
            rent_record_with_renter.refresh_from_db()
            assert rent_record_with_renter.payout_status == "FAILED"
            assert result["status"] == "FAILED"
            assert "Owner not yet registered as beneficiary" in result["message"]
            mock_make_payout.assert_not_called()
            mock_notify_owner_post_payout.assert_not_called()
            mock_send_payout_notification.assert_not_called()

    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_make_payout_exception_returns_failed(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        rent_record_with_renter,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.side_effect = Exception("API error")
            result = process_rent_payout(rent_record_with_renter)
            rent_record_with_renter.refresh_from_db()
            assert rent_record_with_renter.payout_status == "FAILED"
            assert result["status"] == "FAILED"
            assert "API error" in result["message"]
            mock_notify_owner_post_payout.assert_not_called()
            mock_send_payout_notification.assert_not_called()

    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_success_response_updates_status(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        rent_record_with_renter,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.return_value = {"status": "SUCCESS"}
            result = process_rent_payout(rent_record_with_renter)
            rent_record_with_renter.refresh_from_db()
            assert rent_record_with_renter.payout_status == "SUCCESS"
            assert (
                rent_record_with_renter.payout_reference
                == f"rent_{rent_record_with_renter.id}"
            )
            assert result["status"] == "SUCCESS"

    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_failed_response_updates_status(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        rent_record_with_renter,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.return_value = {"status": "FAILED", "message": "error"}
            result = process_rent_payout(rent_record_with_renter)
            rent_record_with_renter.refresh_from_db()
            assert rent_record_with_renter.payout_status == "FAILED"
            assert result["status"] == "FAILED"

    @patch("rentsecure_be.services.cashfree_service.logger")
    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_notify_owner_post_payout_exception_handled(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        mock_logger,
        rent_record_with_renter,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.return_value = {"status": "SUCCESS"}
            mock_notify_owner_post_payout.side_effect = Exception("notify error")
            result = process_rent_payout(rent_record_with_renter)
            assert result["status"] == "SUCCESS"
            mock_logger.warning.assert_called()

    @patch("rentsecure_be.services.cashfree_service.logger")
    @patch("notification.services.rent_notify_service.send_payout_notification")
    @patch("notification.services.rent_notify_service.notify_owner_post_payout")
    @patch("rentsecure_be.services.cashfree_service.make_payout")
    def test_send_payout_notification_exception_handled(
        self,
        mock_make_payout,
        mock_notify_owner_post_payout,
        mock_send_payout_notification,
        mock_logger,
        rent_record_with_renter,
        owner_bank_details,
    ):
        with patch("core.models.OwnerBankDetails") as mock_cls:
            mock_cls.objects.get.return_value = owner_bank_details
            mock_make_payout.return_value = {"status": "SUCCESS"}
            mock_send_payout_notification.side_effect = Exception("notify error")
            result = process_rent_payout(rent_record_with_renter)
            assert result["status"] == "SUCCESS"
            mock_logger.warning.assert_called()


@pytest.mark.django_db
class TestDeleteBeneficiary:
    @patch("rentsecure_be.services.cashfree_service.get_auth_token")
    @patch("rentsecure_be.services.cashfree_service.requests.post")
    def test_success(self, mock_requests_post, mock_get_auth_token):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "SUCCESS"}
        mock_requests_post.return_value = mock_response
        mock_get_auth_token.return_value = "test_token"
        result = delete_beneficiary("bene_123")
        assert result["status"] == "SUCCESS"

    @patch("rentsecure_be.services.cashfree_service.get_auth_token")
    @patch("rentsecure_be.services.cashfree_service.requests.post")
    def test_failure(self, mock_requests_post, mock_get_auth_token):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "FAILED", "message": "Not found"}
        mock_requests_post.return_value = mock_response
        mock_get_auth_token.return_value = "test_token"
        result = delete_beneficiary("bene_123")
        assert result["status"] == "FAILED"

    @patch("rentsecure_be.services.cashfree_service.get_auth_token")
    @patch("rentsecure_be.services.cashfree_service.requests.post")
    def test_network_error(self, mock_requests_post, mock_get_auth_token):
        mock_requests_post.side_effect = Exception("Network error")
        mock_get_auth_token.return_value = "test_token"
        with pytest.raises(Exception, match="Network error"):
            delete_beneficiary("bene_123")
