from datetime import timedelta
from decimal import Decimal
from unittest import mock

import pytest
from rest_framework.test import APIClient

from django.utils import timezone

from core.models import SubscriptionPayment, SubscriptionPlan, UserSubscription


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    from core.models import User

    return User.objects.create_user(
        username="billinguser",
        email="billing@test.com",
        password="testpass123",
        full_name="Billing User",
        phone="+919999999999",
    )


@pytest.fixture
def plan_pro(db):
    return SubscriptionPlan.objects.create(
        name="pro",
        monthly_price=Decimal("29.99"),
        yearly_price=Decimal("299.99"),
        features="Pro features",
        is_active=True,
    )


@pytest.fixture
def plan_elite(db):
    return SubscriptionPlan.objects.create(
        name="elite",
        monthly_price=Decimal("99.99"),
        yearly_price=Decimal("999.99"),
        features="Elite features",
        is_active=True,
    )


def _auth_client(user):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


class TestCreateSubscriptionOrder:
    def test_anonymous_returns_401(self, api_client, plan_pro):
        response = api_client.post(
            "/api/subscription-orders/create/",
            {"plan_id": plan_pro.id, "billing_cycle": "monthly"},
            format="json",
        )
        assert response.status_code == 401

    @mock.patch("core.views.razorpay.Client")
    def test_create_order_for_plan(self, mock_razorpay_client, user, plan_pro):
        mock_client = mock.MagicMock()
        mock_razorpay_client.return_value = mock_client
        mock_client.order.create.return_value = {
            "id": "order_test123",
            "amount": 2999,
            "currency": "INR",
        }

        client = _auth_client(user)
        response = client.post(
            "/api/subscription-orders/create/",
            {"plan_id": plan_pro.id, "billing_cycle": "monthly"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["order_id"] == "order_test123"
        assert SubscriptionPayment.objects.filter(
            razorpay_order_id="order_test123"
        ).exists()

    def test_create_order_missing_plan_id_and_addon(self, user):
        client = _auth_client(user)
        response = client.post(
            "/api/subscription-orders/create/",
            {"billing_cycle": "monthly"},
            format="json",
        )
        assert response.status_code == 400

    def test_create_order_inactive_plan(self, user):
        plan = SubscriptionPlan.objects.create(
            name="inactive",
            monthly_price=Decimal("10"),
            yearly_price=Decimal("100"),
            is_active=False,
        )
        client = _auth_client(user)
        response = client.post(
            "/api/subscription-orders/create/",
            {"plan_id": plan.id, "billing_cycle": "monthly"},
            format="json",
        )
        assert response.status_code == 404


class TestVerifySubscriptionPayment:
    def test_anonymous_returns_401(self, api_client):
        response = api_client.post(
            "/api/subscription-payments/verify/",
            {
                "razorpay_order_id": "order_123",
                "razorpay_payment_id": "pay_123",
                "razorpay_signature": "sig",
            },
            format="json",
        )
        assert response.status_code == 401

    def test_missing_fields_returns_400(self, user):
        client = _auth_client(user)
        response = client.post(
            "/api/subscription-payments/verify/",
            {"razorpay_order_id": "order_123"},
            format="json",
        )
        assert response.status_code == 400

    @mock.patch("core.views.razorpay.Client")
    def test_verify_success_updates_subscription(
        self, mock_razorpay_client, user, plan_pro
    ):
        mock_client = mock.MagicMock()
        mock_razorpay_client.return_value = mock_client
        mock_client.utility.verify_payment_signature.return_value = None
        mock_client.order.fetch.return_value = {"id": "order_123", "status": "paid"}

        subscription = UserSubscription.objects.create(
            user=user, plan=None, is_active=False
        )
        payment = SubscriptionPayment.objects.create(
            user=user,
            subscription=subscription,
            razorpay_order_id="order_123",
            amount=Decimal("29.99"),
            currency="INR",
            status="pending",
            billing_cycle="monthly",
            plan=plan_pro,
        )

        client = _auth_client(user)
        response = client.post(
            "/api/subscription-payments/verify/",
            {
                "razorpay_order_id": "order_123",
                "razorpay_payment_id": "pay_123",
                "razorpay_signature": "valid_sig",
            },
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "success"
        payment.refresh_from_db()
        assert payment.status == "success"
        sub = UserSubscription.objects.get(user=user)
        assert sub.plan == plan_pro


class TestSubscriptionWebhook:
    def test_post_required(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "django.conf.settings.RAZORPAY_WEBHOOK_SECRET", "test_secret"
        )
        response = api_client.get("/api/subscription-webhook/")
        assert response.status_code == 405

    def test_missing_signature_returns_400(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "django.conf.settings.RAZORPAY_WEBHOOK_SECRET", "test_secret"
        )
        response = api_client.post(
            "/api/subscription-webhook/",
            data='{"event": "payment.captured"}',
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_signature_returns_400(self, api_client, monkeypatch):
        monkeypatch.setattr(
            "django.conf.settings.RAZORPAY_WEBHOOK_SECRET", "test_secret"
        )
        body = '{"event": "payment.captured"}'
        import hashlib
        import hmac

        computed = hmac.new(
            b"test_secret", body.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        response = api_client.post(
            "/api/subscription-webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=computed + "X",
        )
        assert response.status_code == 400

    def test_valid_webhook_activates_subscription(
        self, api_client, user, plan_pro, monkeypatch
    ):
        monkeypatch.setattr(
            "django.conf.settings.RAZORPAY_WEBHOOK_SECRET", "test_secret"
        )
        import hashlib
        import hmac
        import json as json_module

        subscription = UserSubscription.objects.create(
            user=user, plan=None, is_active=False
        )
        payment = SubscriptionPayment.objects.create(
            user=user,
            subscription=subscription,
            razorpay_order_id="order_webhook123",
            amount=Decimal("29.99"),
            currency="INR",
            status="pending",
            billing_cycle="monthly",
            plan=plan_pro,
        )

        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "order_id": "order_webhook123",
                        "id": "pay_webhook123",
                    }
                }
            },
        }
        body = json_module.dumps(payload).encode("utf-8")
        computed = hmac.new(b"test_secret", body, hashlib.sha256).hexdigest()
        response = api_client.post(
            "/api/subscription-webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_RAZORPAY_SIGNATURE=computed,
        )
        assert response.status_code == 200
        payment.refresh_from_db()
        assert payment.status == "success"
        sub = UserSubscription.objects.get(user=user)
        assert sub.plan == plan_pro


class TestUserSubscriptionActions:
    def test_upgrade_success(self, user, plan_pro, plan_elite):
        sub = UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.post(
            f"/api/user-subscriptions/{sub.id}/upgrade/",
            {"plan_id": plan_elite.id},
            format="json",
        )
        assert response.status_code == 200
        sub.refresh_from_db()
        assert sub.plan == plan_elite

    def test_upgrade_to_lower_plan_fails(self, user, plan_pro, plan_elite):
        sub = UserSubscription.objects.create(
            user=user, plan=plan_elite, is_active=True
        )
        client = _auth_client(user)
        response = client.post(
            f"/api/user-subscriptions/{sub.id}/upgrade/",
            {"plan_id": plan_pro.id},
            format="json",
        )
        assert response.status_code == 400

    def test_downgrade_success(self, user, plan_pro, plan_elite):
        sub = UserSubscription.objects.create(
            user=user, plan=plan_elite, is_active=True
        )
        client = _auth_client(user)
        response = client.post(
            f"/api/user-subscriptions/{sub.id}/downgrade/",
            {"plan_id": plan_pro.id},
            format="json",
        )
        assert response.status_code == 200
        sub.refresh_from_db()
        assert sub.plan == plan_pro

    def test_cancel_sets_inactive(self, user, plan_pro):
        sub = UserSubscription.objects.create(user=user, plan=plan_pro, is_active=True)
        client = _auth_client(user)
        response = client.post(
            f"/api/user-subscriptions/{sub.id}/cancel/", format="json"
        )
        assert response.status_code == 200
        sub.refresh_from_db()
        assert sub.is_active is False

    def test_renew_extends_end_date(self, user, plan_pro):
        sub = UserSubscription.objects.create(
            user=user,
            plan=plan_pro,
            is_active=True,
            start_date=timezone.now().date() - timedelta(days=60),
            end_date=timezone.now().date() - timedelta(days=30),
        )
        client = _auth_client(user)
        response = client.post(
            f"/api/user-subscriptions/{sub.id}/renew/", format="json"
        )
        assert response.status_code == 200
        sub.refresh_from_db()
        assert sub.end_date >= timezone.now().date()
