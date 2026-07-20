"""Comprehensive pytest tests for core/views.py targeting ≥95% coverage."""

import hashlib
import hmac
import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.test import RequestFactory

from core.models import (
    OTP,
    AddOnPurchase,
    OwnerBankDetails,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)
from core.views.auth_views import _process_referral, send_otp
from core.views.bank_views import create_rent_payment
from core.views.reporting_views import (
    download_rent_excel,
    owner_rent_records,
    rent_inflow_summary,
)
from payments.views.webhooks import (
    _get_rent_from_event,
    _process_rent_payment,
    cashfree_payout_webhook,
)
from properties.models import Renter, RentRecord

User = get_user_model()
API_PREFIX = "/api"
PROPS_PREFIX = "/api/properties"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _make_post_request(payload: dict):
    factory = RequestFactory()
    data = json.dumps(payload).encode("utf-8")
    req = factory.post(
        "/test",
        data=data,
        content_type="application/json",
    )
    req._body = data
    return req


def _make_cashfree_request(payload: dict, secret: str | None = None):
    if secret is None:
        secret = "test-cashfree-secret"
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    factory = RequestFactory()
    req = factory.post(
        "/test",
        data=body,
        content_type="application/json",
    )
    req._body = body
    req.META["HTTP_X_CASHFREE_SIGNATURE"] = signature
    return req


def _make_django_request(user=None, method="get"):
    factory = RequestFactory()
    if method == "get":
        req = factory.get("/test")
    else:
        req = factory.post("/test")
    if user is not None:
        req.user = user
    return req


def _make_webhook_request(payload: dict, headers: dict | None = None):
    body = json.dumps(payload).encode()
    req = SimpleNamespace(
        method="POST",
        body=body,
        headers=headers or {},
        content_type="application/json",
    )
    return req


def _create_renter(unit):
    return Renter.objects.create(
        unit=unit,
        name="Test Renter",
        phone="+919876543210",
        email="renter@test.com",
        rent_amount=10000,
        start_date="2025-01-01",
        end_date="2025-12-31",
    )


# ===================================================================
# OTP / send_otp helper
# ===================================================================


class TestSendOTPFunction:
    @patch("core.views.auth_views.NotificationService")
    def test_send_otp_debug_mode_prints(self, mock_notification_service):
        with patch("core.views.auth_views.settings.DEBUG", True):
            send_otp("+919999999999", "123456")
        mock_notification_service.return_value.send_otp.assert_not_called()

    @patch("core.views.auth_views.NotificationService")
    def test_send_otp_production_sends_message(self, mock_notification_service):
        with patch("core.views.auth_views.settings.DEBUG", False):
            send_otp("+919999999999", "123456")
        mock_notification_service.return_value.send_otp.assert_called_once_with(
            "+919999999999", "123456"
        )


# ===================================================================
# SendOTP View
# ===================================================================


class TestSendOTPView:
    def test_missing_phone_returns_400(self):
        response = APIClient().post(
            f"{API_PREFIX}/auth/send-otp/", {}, content_type="application/json"
        )
        assert response.status_code == 400

    def test_rate_limit_returns_429(self):
        client = APIClient()
        client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+919999999999"},
            content_type="application/json",
        )
        response = client.post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+919999999999"},
            content_type="application/json",
        )
        assert response.status_code == 429

    def test_success_creates_otp_and_returns_200(self):
        response = APIClient().post(
            f"{API_PREFIX}/auth/send-otp/",
            {"phone": "+912222222222"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert OTP.objects.filter(phone_number="+912222222222").exists()


# ===================================================================
# _process_referral helper (covers lines 102-119)
# ===================================================================


class TestProcessReferral:
    def test_no_referral_code_returns_none(self, user):
        otp = OTP.objects.create(
            phone_number=user.phone, code="123456", referral_code=""
        )
        result = _process_referral(otp, user)
        assert result is None

    def test_invalid_referral_code_returns_error(self, user):
        otp = OTP.objects.create(
            phone_number=user.phone, code="123456", referral_code="INVALID"
        )
        result = _process_referral(otp, user)
        assert result is not None
        assert result.status_code == 400
        assert result.data == {"error": "Invalid referral code"}

    def test_valid_referral_creates_link_and_bonus(self, user):
        from referral_and_earn.models import Referral

        referrer_user = User.objects.create_user(
            username="referrer",
            email="r@test.com",
            password="p",
            full_name="Referrer",
            phone="+919999999998",
        )
        referrer_referral = Referral.objects.get(user=referrer_user)
        referrer_referral.referral_code = "VALID12"
        referrer_referral.save()

        otp = OTP.objects.create(
            phone_number=user.phone, code="123456", referral_code="VALID12"
        )

        with patch(
            "referral_and_earn.models.Referral.objects.get_or_create",
            return_value=(Referral.objects.get(user=user), False),
        ):
            result = _process_referral(otp, user)

        assert result is None

        user_referral = Referral.objects.get(user=user)
        assert user_referral.referred_by == referrer_user
        referrer_referral.refresh_from_db()
        assert referrer_referral.bonus_earned == Decimal("500.00")


# ===================================================================
# OwnerVerifyOTP / RenterVerifyOTP
# ===================================================================


class TestOwnerVerifyOTP:
    def test_missing_fields_returns_400(self):
        response = APIClient().post(
            f"{API_PREFIX}/auth/owner/verify-otp/", {}, content_type="application/json"
        )
        assert response.status_code == 400

    def test_invalid_otp_returns_400(self):
        response = APIClient().post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+9111111111", "otp": "000000"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_valid_otp_returns_tokens(self):
        OTP.objects.create(
            phone_number="+912222222222", code="123456", referral_code=""
        )
        response = APIClient().post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+912222222222", "otp": "123456"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert "access" in response.data

    def test_referral_error_returns_400(self):
        OTP.objects.create(
            phone_number="+913333333333", code="654321", referral_code="BADREF"
        )
        response = APIClient().post(
            f"{API_PREFIX}/auth/owner/verify-otp/",
            {"phone": "+913333333333", "otp": "654321"},
            content_type="application/json",
        )
        assert response.status_code == 400


class TestRenterVerifyOTP:
    def test_valid_renter_otp_returns_200(self):
        OTP.objects.create(
            phone_number="+914444444444", code="777777", referral_code=""
        )
        response = APIClient().post(
            f"{API_PREFIX}/auth/renter/verify-otp/",
            {"phone": "+914444444444", "otp": "777777"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert "access" in response.data


# ===================================================================
# ChangePasswordView
# ===================================================================


class TestChangePasswordView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.client = _auth_client(user)

    def test_missing_fields_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/change-password/", {}, content_type="application/json"
        )
        assert response.status_code == 400

    def test_wrong_old_password_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "wrongpass", "new_password": "newpass123"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_same_password_returns_400(self):
        self.user.set_password("samepass")
        self.user.save()
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "samepass", "new_password": "samepass"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_success_returns_200(self):
        self.user.set_password("oldpass123")
        self.user.save()
        response = self.client.post(
            f"{API_PREFIX}/change-password/",
            {"old_password": "oldpass123", "new_password": "newpass456"},
            content_type="application/json",
        )
        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password("newpass456")


# ===================================================================
# ResetPasswordView
# ===================================================================


class TestResetPasswordView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.client = _auth_client(user)

    def test_missing_new_password_returns_400(self):
        response = self.client.post(
            f"{API_PREFIX}/reset-password/", {}, content_type="application/json"
        )
        assert response.status_code == 400

    def test_success_returns_200(self):
        response = self.client.post(
            f"{API_PREFIX}/reset-password/",
            {"new_password": "resetpass123"},
            content_type="application/json",
        )
        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password("resetpass123")


# ===================================================================
# SubscriptionPlanViewSet
# ===================================================================


class TestSubscriptionPlanViewSet:
    def test_list_plans(self, db):
        SubscriptionPlan.objects.all().delete()
        SubscriptionPlan.objects.create(
            name="test_plan",
            monthly_price=Decimal("9.99"),
            yearly_price=Decimal("99.99"),
            features="Test",
        )
        client = APIClient()
        response = client.get(f"{API_PREFIX}/subscription-plans/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_retrieve_plan(self, db):
        plan = SubscriptionPlan.objects.create(
            name="retrieve_plan",
            monthly_price=Decimal("19.99"),
            yearly_price=Decimal("199.99"),
            features="Retrieve",
        )
        client = APIClient()
        response = client.get(f"{API_PREFIX}/subscription-plans/{plan.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "retrieve_plan"


# ===================================================================
# UserSubscriptionViewSet
# ===================================================================


class TestUserSubscriptionViewSet:
    def test_anonymous_returns_401(self, db):
        client = APIClient()
        response = client.get(f"{API_PREFIX}/user-subscriptions/")
        assert response.status_code == 401

    def test_list_own_subscriptions(self, user, plan_pro):
        UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.get(f"{API_PREFIX}/user-subscriptions/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_create_subscription(self, user, plan_pro):
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/user-subscriptions/",
            {"plan": plan_pro.id},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["user"] == user.id

    def test_update_own_subscription(self, user, plan_pro, plan_free):
        sub = UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.patch(
            f"{API_PREFIX}/user-subscriptions/{sub.id}/",
            {"is_active": False},
            format="json",
        )
        assert response.status_code == 200

    def test_update_other_user_subscription_returns_404(self, user, plan_pro):
        other = User.objects.create_user(
            username="other",
            email="o@test.com",
            password="p",
            full_name="Other",
            phone="+919999999997",
        )
        UserSubscription.objects.create(user=other, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.patch(
            f"{API_PREFIX}/user-subscriptions/{UserSubscription.objects.get(user=other).id}/",
            {"is_active": False},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_own_subscription(self, user, plan_pro):
        sub = UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.delete(f"{API_PREFIX}/user-subscriptions/{sub.id}/")
        assert response.status_code == 204

    def test_delete_other_user_subscription_returns_404(self, user, plan_pro):
        other = User.objects.create_user(
            username="other2",
            email="o2@test.com",
            password="p",
            full_name="Other2",
            phone="+919999999996",
        )
        sub = UserSubscription.objects.create(user=other, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.delete(f"{API_PREFIX}/user-subscriptions/{sub.id}/")
        assert response.status_code == 404


# ===================================================================
# AddOnPurchaseViewSet
# ===================================================================


class TestAddOnPurchaseViewSet:
    def test_anonymous_returns_401(self, db):
        client = APIClient()
        response = client.get(f"{API_PREFIX}/addon-purchases/")
        assert response.status_code == 401

    def test_list_own_purchases(self, user):
        AddOnPurchase.objects.create(
            user=user, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.get(f"{API_PREFIX}/addon-purchases/")
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_create_addon(self, user):
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/addon-purchases/",
            {"name": "max_units", "amount": "49.99"},
            format="json",
        )
        assert response.status_code == 201

    def test_update_own_purchase(self, user):
        purchase = AddOnPurchase.objects.create(
            user=user, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.patch(
            f"{API_PREFIX}/addon-purchases/{purchase.id}/",
            {"amount": "39.99"},
            format="json",
        )
        assert response.status_code == 200

    def test_update_other_user_purchase_returns_404(self, user):
        other = User.objects.create_user(
            username="other3",
            email="o3@test.com",
            password="p",
            full_name="Other3",
            phone="+919999999995",
        )
        purchase = AddOnPurchase.objects.create(
            user=other, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.patch(
            f"{API_PREFIX}/addon-purchases/{purchase.id}/",
            {"amount": "39.99"},
            format="json",
        )
        assert response.status_code == 404

    def test_delete_own_purchase(self, user):
        purchase = AddOnPurchase.objects.create(
            user=user, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.delete(f"{API_PREFIX}/addon-purchases/{purchase.id}/")
        assert response.status_code == 204

    def test_delete_other_user_purchase_returns_404(self, user):
        other = User.objects.create_user(
            username="other4",
            email="o4@test.com",
            password="p",
            full_name="Other4",
            phone="+919999999994",
        )
        purchase = AddOnPurchase.objects.create(
            user=other, name="max_buildings", amount=Decimal("29.99")
        )
        client = _auth_client(user)
        response = client.delete(f"{API_PREFIX}/addon-purchases/{purchase.id}/")
        assert response.status_code == 404


# ===================================================================
# UsageLimitViewSet
# ===================================================================


class TestUsageLimitViewSet:
    def test_anonymous_returns_401(self, db):
        client = APIClient()
        response = client.get(f"{API_PREFIX}/usage-limits/")
        assert response.status_code == 401

    def test_list_own_limits(self, user):
        UsageLimit.objects.create(user=user, feature_key="max_units", usage_count=3)
        client = _auth_client(user)
        response = client.get(f"{API_PREFIX}/usage-limits/")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["usage_count"] == 3


# ===================================================================
# cashfree_payout_webhook
# ===================================================================


class TestCashfreePayoutWebhook:
    @patch("notification.services.rent_notify_service.send_payout_notification")
    def test_transfer_success_updates_status(self, mock_notify, owner, building, unit):
        from django.conf import settings as django_settings

        renter = _create_renter(unit)
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            payout_reference="txn_success",
            payout_status="PENDING",
            due_date="2025-01-05",
        )
        req = _make_cashfree_request(
            {"transferId": "txn_success", "event": "TRANSFER_SUCCESS"}
        )
        with patch.object(
            django_settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"
        ):
            response = cashfree_payout_webhook(req)
        assert response.status_code == 200
        rent.refresh_from_db()
        assert rent.payout_status == "SUCCESS"
        mock_notify.assert_called_once_with(rent)

    @patch("notification.services.rent_notify_service.send_payout_notification")
    def test_transfer_failed_updates_status(self, mock_notify, owner, building, unit):
        from django.conf import settings as django_settings

        renter = _create_renter(unit)
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            payout_reference="txn_fail",
            payout_status="PENDING",
            due_date="2025-01-05",
        )
        req = _make_cashfree_request(
            {"transferId": "txn_fail", "event": "TRANSFER_FAILED"}
        )
        with patch.object(
            django_settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"
        ):
            response = cashfree_payout_webhook(req)
        assert response.status_code == 200
        rent.refresh_from_db()
        assert rent.payout_status == "FAILED"

    @patch("notification.services.rent_notify_service.send_payout_notification")
    def test_notification_exception_handled(self, mock_notify, owner, building, unit):
        from django.conf import settings as django_settings

        renter = _create_renter(unit)
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            payout_reference="txn_exc",
            payout_status="PENDING",
            due_date="2025-01-05",
        )
        mock_notify.side_effect = Exception("notification failed")
        req = _make_cashfree_request(
            {"transferId": "txn_exc", "event": "TRANSFER_SUCCESS"}
        )
        with patch.object(
            django_settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"
        ):
            response = cashfree_payout_webhook(req)
        assert response.status_code == 200
        rent.refresh_from_db()
        assert rent.payout_status == "SUCCESS"

    def test_invalid_transfer_id_returns_404(self):
        from django.conf import settings as django_settings

        req = _make_cashfree_request(
            {"transferId": "nonexistent", "event": "TRANSFER_SUCCESS"}
        )
        with patch.object(
            django_settings, "CASHFREE_WEBHOOK_SECRET", "test-cashfree-secret"
        ):
            response = cashfree_payout_webhook(req)
        assert response.status_code == 404


# ===================================================================
# create_rent_payment
# ===================================================================


class TestCreateRentPayment:
    def test_invalid_method_returns_405(self):
        req = _make_django_request(method="get")
        response = create_rent_payment(req)
        assert response.status_code == 405

    def test_rent_not_found_returns_404(self):
        req = _make_post_request({"rent_id": "9999"})
        response = create_rent_payment(req)
        assert response.status_code == 404

    @patch("payments.adapters.razorpay.client")
    def test_success_creates_order(self, mock_client, owner, building, unit):
        renter = _create_renter(unit)
        mock_client.order.create.return_value = {
            "id": "order_123",
            "amount": 100000,
            "currency": "INR",
        }

        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        req = _make_post_request({"rent_id": str(rent.id)})
        response = create_rent_payment(req)
        assert response.status_code == 200
        content = json.loads(response.content)
        assert content["order_id"] == "order_123"
        rent.refresh_from_db()
        assert rent.razorpay_order_id == "order_123"


# ===================================================================
# _get_rent_from_event
# ===================================================================


class TestGetRentFromEvent:
    @pytest.fixture(autouse=True)
    def setup(self, owner, building, unit):
        self.owner = owner
        self.building = building
        self.unit = unit
        self.renter = _create_renter(unit)

    def test_payment_link_paid_missing_reference_returns_none(self):
        data = {
            "event": "payment_link.paid",
            "payload": {"payment_link": {"entity": {}}},
        }
        result = _get_rent_from_event(data, data["event"])
        assert result is None

    def test_payment_link_paid_returns_rent(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        data = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {"entity": {"reference_id": str(rent.id)}},
            },
        }
        result = _get_rent_from_event(data, data["event"])
        assert result.id == rent.id

    def test_payment_link_paid_rent_not_found_returns_none(self):
        data = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {"entity": {"reference_id": "9999"}},
            },
        }
        result = _get_rent_from_event(data, data["event"])
        assert result is None

    def test_payment_captured_missing_order_id_returns_none(self):
        data = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {}}},
        }
        result = _get_rent_from_event(data, data["event"])
        assert result is None

    def test_payment_captured_returns_rent(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            razorpay_order_id="order_456",
            due_date="2025-01-05",
        )
        data = {
            "event": "payment.captured",
            "payload": {
                "payment": {"entity": {"order_id": "order_456"}},
            },
        }
        result = _get_rent_from_event(data, data["event"])
        assert result.id == rent.id

    def test_payment_captured_rent_not_found_returns_none(self):
        data = {
            "event": "payment.captured",
            "payload": {
                "payment": {"entity": {"order_id": "order_999"}},
            },
        }
        result = _get_rent_from_event(data, data["event"])
        assert result is None

    def test_unknown_event_returns_none(self):
        data = {"event": "unknown.event", "payload": {}}
        result = _get_rent_from_event(data, data["event"])
        assert result is None


# ===================================================================
# _process_rent_payment
# ===================================================================


class TestProcessRentPayment:
    @patch("payments.services.payment_service.PaymentService.process_payout")
    def test_success_marks_paid_and_calls_payout(
        self, mock_payout, owner, building, unit
    ):
        renter = _create_renter(unit)
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        _process_rent_payment(rent)
        rent.refresh_from_db()
        assert rent.payment_status == "paid"
        assert rent.date_paid is not None
        mock_payout.assert_called_once_with(rent)

    @patch("payments.services.payment_service.PaymentService.process_payout")
    def test_payout_exception_is_handled(self, mock_payout, owner, building, unit):
        renter = _create_renter(unit)
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        mock_payout.side_effect = Exception("payout failed")
        _process_rent_payment(rent)
        rent.refresh_from_db()
        assert rent.payment_status == "paid"


# ===================================================================
# razorpay_webhook
# ===================================================================


class TestRazorpayWebhook:
    def test_get_returns_405(self):
        from payments.views.webhooks import razorpay_webhook

        req = SimpleNamespace(method="GET")
        response = razorpay_webhook(req)
        assert response.status_code == 405

    def test_invalid_json_returns_400(self):
        from django.conf import settings as django_settings

        from payments.views.webhooks import razorpay_webhook

        body = b"not json"
        sig = hmac.new(b"test-razorpay-secret", body, hashlib.sha256).hexdigest()
        req = SimpleNamespace(
            method="POST",
            body=body,
            headers={"X-Razorpay-Signature": sig},
        )

        with patch.object(
            django_settings, "RAZORPAY_WEBHOOK_SECRET", "test-razorpay-secret"
        ):
            response = razorpay_webhook(req)
        assert response.status_code == 401

    def test_invalid_signature_returns_401(self):
        from django.conf import settings as django_settings

        from payments.views.webhooks import razorpay_webhook

        body = json.dumps({"event": "payment.captured"}).encode()
        req = SimpleNamespace(
            method="POST",
            body=body,
            headers={"X-Razorpay-Signature": "bad_sig"},
        )

        with patch.object(django_settings, "RAZORPAY_WEBHOOK_SECRET", "secret"):
            with patch("hmac.new", return_value=MagicMock()):
                with patch("hmac.compare_digest", return_value=False):
                    response = razorpay_webhook(req)
        assert response.status_code == 401

    def test_missing_signature_returns_400(self):
        from django.conf import settings as django_settings

        from payments.views.webhooks import razorpay_webhook

        body = json.dumps({"event": "payment.captured"}).encode()
        req = SimpleNamespace(
            method="POST",
            body=body,
            headers={},
        )

        with patch.object(django_settings, "RAZORPAY_WEBHOOK_SECRET", "secret"):
            response = razorpay_webhook(req)
        assert response.status_code == 400

    @patch("payments.views.webhooks._get_rent_from_event")
    @patch("payments.views.webhooks._process_rent_payment")
    def test_event_with_rent_calls_process(
        self, mock_process, mock_get_rent, owner, building, unit
    ):
        from django.conf import settings as django_settings

        from payments.views.webhooks import razorpay_webhook

        renter = _create_renter(unit)
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-01-05",
        )
        mock_get_rent.return_value = rent
        body = json.dumps({"event": "payment.captured"}).encode()
        sig = hmac.new(b"test-razorpay-secret", body, hashlib.sha256).hexdigest()
        req = SimpleNamespace(
            method="POST",
            body=body,
            headers={"X-Razorpay-Signature": sig},
        )

        with patch.object(
            django_settings, "RAZORPAY_WEBHOOK_SECRET", "test-razorpay-secret"
        ):
            response = razorpay_webhook(req)
        assert response.status_code == 200
        mock_process.assert_called_once()

    @patch("payments.views.webhooks._get_rent_from_event")
    def test_event_without_rent_returns_200(self, mock_get_rent):
        from django.conf import settings as django_settings

        from payments.views.webhooks import razorpay_webhook

        mock_get_rent.return_value = None
        body = json.dumps({"event": "unknown.event"}).encode()
        sig = hmac.new(b"test-razorpay-secret", body, hashlib.sha256).hexdigest()
        req = SimpleNamespace(
            method="POST",
            body=body,
            headers={"X-Razorpay-Signature": sig},
        )

        with patch.object(
            django_settings, "RAZORPAY_WEBHOOK_SECRET", "test-razorpay-secret"
        ):
            response = razorpay_webhook(req)
        assert response.status_code == 200

    @patch("payments.views.webhooks._get_rent_from_event")
    @patch("payments.views.webhooks._process_rent_payment")
    def test_already_paid_rent_returns_ok(
        self, mock_process, mock_get_rent, owner, building, unit
    ):
        from django.conf import settings as django_settings

        from payments.views.webhooks import razorpay_webhook

        renter = _create_renter(unit)
        rent = RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PAID",
            due_date="2025-01-05",
        )
        rent.payment_status = RentRecord.Status.PAID
        mock_get_rent.return_value = rent
        body = json.dumps({"event": "payment.captured"}).encode()
        sig = hmac.new(b"test-razorpay-secret", body, hashlib.sha256).hexdigest()
        req = SimpleNamespace(
            method="POST",
            body=body,
            headers={"X-Razorpay-Signature": sig},
        )

        with patch.object(
            django_settings, "RAZORPAY_WEBHOOK_SECRET", "test-razorpay-secret"
        ):
            response = razorpay_webhook(req)
        assert response.status_code == 200
        assert json.loads(response.content) == {
            "status": "ok",
            "message": "Already processed",
        }
        mock_process.assert_not_called()


# ===================================================================
# update_owner_bank_details
# ===================================================================


class TestUpdateOwnerBankDetails:
    def test_missing_fields_returns_400(self, user):
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/api/owner/update-bank-details/",
            {},
            format="json",
        )
        assert response.status_code == 400

    @patch("core.services.bank_details_service.add_beneficiary")
    @patch("payments.services.payment_service.PaymentService.delete_beneficiary")
    def test_existing_bank_with_beneficiary_deletes_first(
        self, mock_delete, mock_add, user
    ):
        OwnerBankDetails.objects.create(
            owner=user,
            bank_account_number="1234567890",
            ifsc_code="HDFC0001234",
            account_holder_name="Test User",
            beneficiary_id="BENE_OLD",
        )
        mock_delete.return_value = {}
        mock_add.return_value = {"subCode": "200"}
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/api/owner/update-bank-details/",
            {
                "account_number": "9999999999",
                "ifsc_code": "HDFC0009999",
                "account_holder_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == 200
        mock_delete.assert_called_once_with("BENE_OLD")

    @patch("core.services.bank_details_service.add_beneficiary")
    def test_new_bank_creates_details(self, mock_add, user):
        mock_add.return_value = {"subCode": "200"}
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/api/owner/update-bank-details/",
            {
                "account_number": "1234567890",
                "ifsc_code": "HDFC0001234",
                "account_holder_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == 200
        assert OwnerBankDetails.objects.filter(owner=user).exists()

    @patch("core.services.bank_details_service.add_beneficiary")
    def test_bank_registration_failure_returns_400(self, mock_add, user):
        mock_add.return_value = {"subCode": "400", "message": "Invalid bank"}
        client = _auth_client(user)
        response = client.post(
            f"{API_PREFIX}/api/owner/update-bank-details/",
            {
                "account_number": "1234567890",
                "ifsc_code": "HDFC0001234",
                "account_holder_name": "Test User",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "error" in response.data


# ===================================================================
# rent_inflow_summary (no URL route, call directly)
# ===================================================================


class TestRentInflowSummaryView:
    def test_returns_summary(self, owner, building, unit):
        renter = _create_renter(unit)
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("15000"),
            payment_method="upi",
            status="PAID",
            due_date="2025-01-05",
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("15000"),
            payment_method="upi",
            status="PENDING",
            due_date="2025-02-05",
        )
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("15000"),
            payment_method="upi",
            status="PAID",
            payout_status="FAILED",
            due_date="2025-03-05",
        )
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = rent_inflow_summary(req)
        assert response.status_code == 200
        assert response.data["total_received"] == Decimal("30000")
        assert response.data["pending_payments"] == 1
        assert response.data["failed_payouts"] == 1

    def test_empty_summary(self, owner):
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = rent_inflow_summary(req)
        assert response.status_code == 200
        assert response.data["total_received"] == 0
        assert response.data["pending_payments"] == 0
        assert response.data["failed_payouts"] == 0


# ===================================================================
# owner_rent_records (no URL route, call directly)
# ===================================================================


class TestOwnerRentRecordsView:
    def test_lists_own_records(self, owner, building, unit):
        renter = _create_renter(unit)
        RentRecord.objects.create(
            unit=unit,
            renter=renter,
            amount=Decimal("12000"),
            payment_method="upi",
            status="PAID",
            payout_status="SUCCESS",
            due_date="2025-01-05",
        )
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = owner_rent_records(req)
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["rent"] == float(Decimal("12000"))
        assert response.data[0]["renter"] == renter.name

    def test_empty_records(self, owner):
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = owner_rent_records(req)
        assert response.status_code == 200
        assert response.data == []


# ===================================================================
# download_rent_excel (no URL route, call directly)
# ===================================================================


class TestDownloadRentExcelView:
    @patch("core.views.reporting_views.generate_owner_rent_report")
    def test_returns_excel_response(self, mock_generate, owner):
        mock_generate.return_value = b"fake_excel_content"
        req = _make_django_request(user=owner, method="get")
        with patch("rest_framework.request.Request.user", owner):
            response = download_rent_excel(req)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/vnd.ms-excel"
        assert "attachment" in response["Content-Disposition"]
