"""
End-to-End API Flow Tests for RentSecureBE

These tests validate complete business flows through the REST API,
simulating real client behavior without mocking the application layers.

Run with:
    pytest tests/test_e2e_flows/ -v --tb=short --randomly-seed=last
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import AddOnPurchase as AddOnPurchase
from core.models import NotificationPreference as NotificationPreference
from core.models import OwnerBankDetails as OwnerBankDetails
from core.models import PlanFeatureLimit as PlanFeatureLimit
from core.models import SubscriptionPlan as SubscriptionPlan
from core.models import UserSubscription as UserSubscription
from notification.models import DeviceToken as DeviceToken
from notification.models import Notification as Notification
from properties.models import Building as Building
from properties.models import Caretaker as Caretaker
from properties.models import ExtraCharge as ExtraCharge
from properties.models import Renter as Renter
from properties.models import RentRecord as RentRecord
from properties.models import Unit as Unit
from properties.models.caretaker_models import CareTaker as CareTaker

User = get_user_model()

API_PREFIX = "/api"

# ---------------------------------------------------------------------------
# Deterministic test users
# ---------------------------------------------------------------------------

OWNER_USERNAME = "e2e_owner"
OWNER_PASSWORD = "E2eOwnerPass123!"
OWNER_EMAIL = "e2e_owner@rentsecure.test"

RENTER_USERNAME = "e2e_renter"
RENTER_PASSWORD = "E2eRenterPass123!"
RENTER_EMAIL = "e2e_renter@rentsecure.test"

CARETAKER_USERNAME = "e2e_caretaker"
CARETAKER_PASSWORD = "E2eCaretakerPass123!"
CARETAKER_EMAIL = "e2e_caretaker@rentsecure.test"

UNAUTHORIZED_USERNAME = "e2e_unauthorized"
UNAUTHORIZED_PASSWORD = "E2eUnauthPass123!"


# ---------------------------------------------------------------------------
# Base mixin with shared helpers
# ---------------------------------------------------------------------------


class E2EAPIClientMixin:
    """Mixin providing authenticated API client helpers for E2E flows."""

    def _force_auth(self, user):
        self.client.force_authenticate(user=user)

    def _get_access_token(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def _auth_header(self, token: str) -> dict:
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _post_json(self, url, data=None, user=None, token=None):
        if user:
            token = token or self._get_access_token(user)
        headers = self._auth_header(token) if token else {}
        return self.client.post(url, data, format="json", **headers)

    def _get_json(self, url, user=None, token=None):
        if user:
            token = token or self._get_access_token(user)
        headers = self._auth_header(token) if token else {}
        return self.client.get(url, **headers)

    def _patch_json(self, url, data=None, user=None, token=None):
        if user:
            token = token or self._get_access_token(user)
        headers = self._auth_header(token) if token else {}
        return self.client.patch(url, data, format="json", **headers)

    def _delete_json(self, url, user=None, token=None):
        if user:
            token = token or self._get_access_token(user)
        headers = self._auth_header(token) if token else {}
        return self.client.delete(url, **headers)

    def _create_owner_with_subscription(self, username, plan_name="pro"):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@rentsecure.test",
            password="TestPass123!",
            full_name=f"E2E {username}",
            phone=f"+91987654{username[-4:]}",
            is_active=True,
        )
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name=plan_name,
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": f"{plan_name} plan",
                "is_active": True,
            },
        )
        limits = {
            "max_buildings": "unlimited",
            "max_units": "unlimited",
            "max_renters": "unlimited",
            "max_caretakers": "unlimited",
            "unit_images": "unlimited",
            "unit_documents": "unlimited",
            "rent_agreement_drafts": "unlimited",
            "rent_records": "unlimited",
            "ai_chat_messages": "unlimited",
            "tax_notifications": "yes",
            "whatsapp_alerts": "yes",
            "export_pdf_dossier": "yes",
        }
        for feature_key, value in limits.items():
            PlanFeatureLimit.objects.get_or_create(
                plan=plan, feature_key=feature_key, defaults={"value": value}
            )
        UserSubscription.objects.create(
            user=user,
            plan=plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
            is_yearly=False,
        )
        return user

    def _create_renter_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@rentsecure.test",
            password="TestPass123!",
            full_name=f"E2E {username}",
            phone=f"+91987654{username[-4:]}",
            is_active=True,
        )

    def _ensure_group(self, user, group_name):
        from django.contrib.auth.models import Group

        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

    def _create_complete_owner_data(self, owner):
        import uuid

        suffix = str(uuid.uuid4())[:8]
        building = Building.objects.create(
            owner=owner,
            name=f"E2E Test Building {suffix}",
            address_line=f"123 E2E Street {suffix}",
            city="Test City",
            state="TS",
            country="IN",
            postal_code="400001",
            is_archived=False,
        )
        unit = Unit.objects.create(
            owner=owner,
            building=building,
            unit=f"E2E-101-{suffix}",
            address_line=f"123 E2E Street {suffix}",
            city="Test City",
            state="TS",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
            status="vacant",
            is_vacant=True,
            rent_amount=Decimal("15000.00"),
        )
        renter_user = self._create_renter_user(f"{RENTER_USERNAME}_{suffix}")
        self._ensure_group(renter_user, "renter")
        renter = Renter.objects.create(
            unit=unit,
            name="E2E Renter",
            phone=f"+91987654{suffix[-4:]}",
            email=f"{RENTER_USERNAME}_{suffix}@rentsecure.test",
            user=renter_user,
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() + timedelta(days=335),
            rent_amount=Decimal("15000.00"),
            is_active=True,
            status=Renter.RenterStatus.ACTIVE,
        )
        caretaker_user = self._create_renter_user(f"{CARETAKER_USERNAME}_{suffix}")
        self._ensure_group(caretaker_user, "tenant")
        caretaker = CareTaker.objects.create(
            unit=unit,
            name="E2E Caretaker",
            phone=f"+91987655{suffix[-4:]}",
            email=f"{CARETAKER_USERNAME}_{suffix}@rentsecure.test",
            joining_date=timezone.now().date() - timedelta(days=60),
            leaving_date=timezone.now().date() + timedelta(days=180),
            is_active=True,
        )
        return {
            "owner": owner,
            "building": building,
            "unit": unit,
            "renter": renter,
            "renter_user": renter_user,
            "caretaker": caretaker,
            "caretaker_user": caretaker_user,
        }
