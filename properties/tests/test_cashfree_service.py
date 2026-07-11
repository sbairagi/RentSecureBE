"""Tests for rentsecure_be services."""

from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import OwnerBankDetails
from properties.models import Building, Renter, RentRecord, Unit
from rentsecure_be.services.cashfree_service import (
    delete_beneficiary,
    pay_owner_after_rent,
    process_rent_payout,
    register_cashfree_beneficiary,
    register_owner_with_cashfree,
)

User = get_user_model()


class RegisterOwnerWithCashfreeTest(TestCase):
    def test_register_owner_success(self):
        owner = User.objects.create_user(
            username="owner1",
            email="o1@test.com",
            password="p",
            full_name="Owner",
            phone="+91",
        )
        bank_details = OwnerBankDetails.objects.create(
            owner=owner,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
        )
        with patch(
            "rentsecure_be.services.cashfree_service.add_beneficiary"
        ) as mock_add:
            mock_add.return_value = {"status": "SUCCESS"}
            register_owner_with_cashfree(bank_details)
            bank_details.refresh_from_db()
            self.assertEqual(bank_details.beneficiary_id, f"owner_{bank_details.id}")
            self.assertTrue(bank_details.bank_account_verified)

    def test_register_owner_invalid_type(self):
        with self.assertRaises(TypeError):
            register_owner_with_cashfree("not an owner")


class RegisterCashfreeBeneficiaryTest(TestCase):
    def test_register_beneficiary_success(self):
        owner = User.objects.create_user(
            username="owner2",
            email="o2@test.com",
            password="p",
            full_name="Owner2",
            phone="+91",
        )
        bank_details = OwnerBankDetails.objects.create(
            owner=owner,
            bank_account_number="9876543210",
            ifsc_code="ICIC0005678",
        )
        with patch(
            "rentsecure_be.services.cashfree_service.add_beneficiary"
        ) as mock_add:
            mock_add.return_value = {"status": "SUCCESS"}
            result = register_cashfree_beneficiary(bank_details)
            self.assertEqual(result["status"], "SUCCESS")
            bank_details.refresh_from_db()
            self.assertTrue(bank_details.bank_account_verified)

    def test_register_beneficiary_invalid_type(self):
        with self.assertRaises(TypeError):
            register_cashfree_beneficiary("invalid")


class PayOwnerAfterRentTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="pay_owner",
            email="po@test.com",
            password="p",
            full_name="Pay Owner",
            phone="+91",
        )
        self.renter_user = User.objects.create_user(
            username="pay_renter",
            email="pr@test.com",
            password="p",
            full_name="Pay Renter",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="Pay Building",
            address_line="123 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            unit_type="1bhk",
            rent_amount=15000,
            is_vacant=False,
        )
        self.renter_model = Renter.objects.create(
            unit=self.unit,
            name="Test Renter",
            phone="+911234567890",
            email="tr@test.com",
            start_date="2024-01-01",
            end_date="2024-12-31",
            rent_amount=15000,
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter_model,
            amount=15000,
            payment_method="upi",
            status="paid",
            paid_on=date(2024, 1, 5),
            due_date=date(2024, 1, 5),
            late_fee=0,
            discount=0,
            payout_status="PENDING",
        )

    def test_pay_owner_after_rent_already_paid(self):
        self.rent.payout_status = "SUCCESS"
        self.rent.save()
        result = pay_owner_after_rent(self.rent)
        self.assertEqual(result["status"], "ALREADY_PAID")

    def test_pay_owner_after_rent_no_owner(self):
        self.rent.renter = None
        self.rent.save()
        with self.assertRaises(ValueError):
            pay_owner_after_rent(self.rent)

    def test_pay_owner_after_rent_no_bank_details(self):
        with patch(
            "rentsecure_be.services.cashfree_service.make_payout"
        ) as mock_payout:
            mock_payout.return_value = {"status": "SUCCESS"}
            with self.assertRaises(ValueError):
                pay_owner_after_rent(self.rent)


class ProcessRentPayoutTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="proc_owner",
            email="pro@test.com",
            password="p",
            full_name="Proc Owner",
            phone="+91",
        )
        self.renter_user = User.objects.create_user(
            username="proc_renter",
            email="prr@test.com",
            password="p",
            full_name="Proc Renter",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="Proc Building",
            address_line="456 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="102",
            address_line="456 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            unit_type="1bhk",
            rent_amount=20000,
            is_vacant=False,
        )
        self.renter_model = Renter.objects.create(
            unit=self.unit,
            name="Proc Renter",
            phone="+911234567890",
            email="prr@test.com",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            rent_amount=20000,
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter_model,
            amount=20000,
            payment_method="upi",
            status="paid",
            paid_on=date(2024, 1, 5),
            due_date=date(2024, 1, 5),
            late_fee=0,
            discount=0,
            payout_status="PENDING",
        )

    def test_process_payout_success(self):
        OwnerBankDetails.objects.create(
            owner=self.owner,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
            beneficiary_id="bene_123",
        )
        with patch(
            "rentsecure_be.services.cashfree_service.make_payout"
        ) as mock_payout:
            mock_payout.return_value = {"status": "SUCCESS"}
            import notification.services.rent_notify_service as rns_module

            original_notify = rns_module.notify_owner_post_payout
            original_send = rns_module.send_payout_notification
            rns_module.notify_owner_post_payout = lambda rent: None
            rns_module.send_payout_notification = lambda rent: None
            try:
                import rentsecure_be.services.cashfree_service as cs_module

                cs_module.RentRecord = RentRecord
                try:
                    result = process_rent_payout(self.rent)
                    self.assertEqual(result["status"], "SUCCESS")
                    self.rent.refresh_from_db()
                    self.assertEqual(self.rent.payout_status, "SUCCESS")
                finally:
                    if hasattr(cs_module, "RentRecord"):
                        delattr(cs_module, "RentRecord")
            finally:
                rns_module.notify_owner_post_payout = original_notify
                rns_module.send_payout_notification = original_send

    def test_process_payout_no_bank_details(self):
        with patch(
            "rentsecure_be.services.cashfree_service.make_payout"
        ) as mock_payout:
            mock_payout.return_value = {"status": "SUCCESS"}
            import rentsecure_be.services.cashfree_service as cs_module

            cs_module.RentRecord = RentRecord
            try:
                result = process_rent_payout(self.rent)
                self.assertEqual(result["status"], "FAILED")
            finally:
                if hasattr(cs_module, "RentRecord"):
                    delattr(cs_module, "RentRecord")


class DeleteBeneficiaryTest(TestCase):
    @patch("rentsecure_be.services.cashfree_service.requests")
    @patch("rentsecure_be.services.cashfree_service.get_auth_token")
    def test_delete_beneficiary(self, mock_token, mock_requests):
        mock_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "SUCCESS"}
        mock_requests.post.return_value = mock_response
        result = delete_beneficiary("bene_123")
        self.assertEqual(result["status"], "SUCCESS")
        mock_requests.post.assert_called_once()


class RegisterOwnerWithCashfreeFailureTest(TestCase):
    def test_register_owner_failure(self):
        owner = User.objects.create_user(
            username="owner_fail",
            email="of@test.com",
            password="p",
            full_name="Owner Fail",
            phone="+91",
        )
        bank_details = OwnerBankDetails.objects.create(
            owner=owner,
            bank_account_number="9999999999",
            ifsc_code="HDFC0001234",
        )
        with patch(
            "rentsecure_be.services.cashfree_service.add_beneficiary"
        ) as mock_add:
            mock_add.return_value = {"status": "FAILED"}
            register_owner_with_cashfree(bank_details)
            bank_details.refresh_from_db()
            self.assertEqual(bank_details.beneficiary_id, "")
            self.assertFalse(bank_details.bank_account_verified)


class PayOwnerAfterRentFailureTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="pay_fail_owner",
            email="pfo@test.com",
            password="p",
            full_name="PayFailOwner",
            phone="+91",
        )
        self.renter_user = User.objects.create_user(
            username="pay_fail_renter",
            email="pfr@test.com",
            password="p",
            full_name="PayFailRenter",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="Fail Building",
            address_line="123 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            unit_type="1bhk",
            rent_amount=15000,
            is_vacant=False,
        )
        self.renter_model = Renter.objects.create(
            unit=self.unit,
            name="Fail Renter",
            phone="+911234567890",
            email="fr@test.com",
            start_date="2024-01-01",
            end_date="2024-12-31",
            rent_amount=15000,
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter_model,
            amount=15000,
            payment_method="upi",
            status="paid",
            paid_on=date(2024, 1, 5),
            due_date=date(2024, 1, 5),
            late_fee=0,
            discount=0,
            payout_status="PENDING",
        )

    def test_pay_owner_after_rent_payout_failure(self):
        OwnerBankDetails.objects.create(
            owner=self.owner,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
            beneficiary_id="bene_123",
        )
        with patch(
            "rentsecure_be.services.cashfree_service.make_payout"
        ) as mock_payout:
            mock_payout.return_value = {"status": "FAILED"}
            with patch("notification.services.rent_notify_service.notify_renter"):
                with patch("notification.services.rent_notify_service.notify_owner"):
                    with patch(
                        "rentsecure_be.services.cashfree_service._send_whatsapp_payout_alert"
                    ):
                        with patch(
                            "notification.services.rent_notify_service.send_payout_notification"
                        ):
                            result = pay_owner_after_rent(self.rent)
                            self.assertEqual(result["status"], "FAILED")
                            self.rent.refresh_from_db()
                            self.assertEqual(self.rent.payout_status, "FAILED")

    def test_pay_owner_after_rent_no_renter(self):
        self.rent.renter = None
        self.rent.save()
        with self.assertRaises(ValueError):
            pay_owner_after_rent(self.rent)


class ProcessRentPayoutEdgeCasesTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="proc_edge_owner",
            email="peo@test.com",
            password="p",
            full_name="ProcEdgeOwner",
            phone="+91",
        )
        self.renter_user = User.objects.create_user(
            username="proc_edge_renter",
            email="per@test.com",
            password="p",
            full_name="ProcEdgeRenter",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="Edge Building",
            address_line="456 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="102",
            address_line="456 Main St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            unit_type="1bhk",
            rent_amount=20000,
            is_vacant=False,
        )
        self.renter_model = Renter.objects.create(
            unit=self.unit,
            name="ProcEdge Renter",
            phone="+911234567890",
            email="per@test.com",
            start_date=date(2024, 1, 1),
            end_date="2024-12-31",
            rent_amount=20000,
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter_model,
            amount=20000,
            payment_method="upi",
            status="paid",
            paid_on=date(2024, 1, 5),
            due_date=date(2024, 1, 5),
            late_fee=0,
            discount=0,
            payout_status="PENDING",
        )

    def test_process_payout_no_beneficiary_id(self):
        OwnerBankDetails.objects.create(
            owner=self.owner,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
        )
        import notification.services.rent_notify_service as rns_module

        rns_module.notify_owner_post_payout = lambda rent: None
        rns_module.send_payout_notification = lambda rent: None
        import rentsecure_be.services.cashfree_service as cs_module

        cs_module.RentRecord = RentRecord
        try:
            result = process_rent_payout(self.rent)
            self.assertEqual(result["status"], "FAILED")
            self.rent.refresh_from_db()
            self.assertEqual(self.rent.payout_status, "FAILED")
        finally:
            if hasattr(cs_module, "RentRecord"):
                delattr(cs_module, "RentRecord")

    def test_process_payout_api_exception(self):
        OwnerBankDetails.objects.create(
            owner=self.owner,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
            beneficiary_id="bene_123",
        )
        with patch(
            "rentsecure_be.services.cashfree_service.make_payout",
            side_effect=Exception("API error"),
        ):
            import notification.services.rent_notify_service as rns_module

            original_notify = rns_module.notify_owner_post_payout
            original_send = rns_module.send_payout_notification
            rns_module.notify_owner_post_payout = lambda rent: None
            rns_module.send_payout_notification = lambda rent: None
            try:
                import rentsecure_be.services.cashfree_service as cs_module

                cs_module.RentRecord = RentRecord
                try:
                    result = process_rent_payout(self.rent)
                    self.assertEqual(result["status"], "FAILED")
                    self.rent.refresh_from_db()
                    self.assertEqual(self.rent.payout_status, "FAILED")
                finally:
                    if hasattr(cs_module, "RentRecord"):
                        delattr(cs_module, "RentRecord")
            finally:
                rns_module.notify_owner_post_payout = original_notify
                rns_module.send_payout_notification = original_send

    def test_process_payout_notify_exceptions(self):
        OwnerBankDetails.objects.create(
            owner=self.owner,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
            beneficiary_id="bene_123",
        )
        with patch(
            "rentsecure_be.services.cashfree_service.make_payout"
        ) as mock_payout:
            mock_payout.return_value = {"status": "SUCCESS"}

            failure_count = {"notify": 0, "send": 0}

            def failing_notify(rent):
                failure_count["notify"] += 1
                raise Exception("notify failed")

            def failing_send(rent):
                failure_count["send"] += 1
                raise Exception("send failed")

            import notification.services.rent_notify_service as rns_module
            import rentsecure_be.services.cashfree_service as cs_module

            original_notify = rns_module.notify_owner_post_payout
            original_send = rns_module.send_payout_notification
            rns_module.notify_owner_post_payout = failing_notify
            rns_module.send_payout_notification = failing_send
            cs_module.RentRecord = RentRecord
            try:
                result = process_rent_payout(self.rent)
                self.assertEqual(result["status"], "SUCCESS")
                self.rent.refresh_from_db()
                self.assertEqual(self.rent.payout_status, "SUCCESS")
                self.assertEqual(failure_count["notify"], 1)
                self.assertEqual(failure_count["send"], 1)
            finally:
                rns_module.notify_owner_post_payout = original_notify
                rns_module.send_payout_notification = original_send
                if hasattr(cs_module, "RentRecord"):
                    delattr(cs_module, "RentRecord")


class DeleteBeneficiaryFailureTest(TestCase):
    @patch("rentsecure_be.services.cashfree_service.requests")
    @patch("rentsecure_be.services.cashfree_service.get_auth_token")
    def test_delete_beneficiary_failure(self, mock_token, mock_requests):
        mock_token.return_value = "test-token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "FAILED"}
        mock_requests.post.return_value = mock_response
        result = delete_beneficiary("bene_999")
        self.assertEqual(result["status"], "FAILED")
        mock_requests.post.assert_called_once()
